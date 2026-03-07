from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Chat, Message, Character, User, Persona, MessageRole, LoreEntry
from app.chat.prompt_builder import build_system_prompt
from app.db.session import engine as db_engine
from app.llm.base import LLMMessage

MAX_CONTEXT_MESSAGES = 50
DEFAULT_CONTEXT_TOKENS = 24000  # ~6k real tokens; Russian text needs ~4 chars/token

# Post-history reminder — injected AFTER chat history, closest to generation point.
# Short (~50 tokens) reinforcement of key rules. Most effective position per SillyTavern research.
_FICTION_POST_HISTORY = {
    "ru": (
        "[Продолжай историю от второго лица. Сохраняй текущую локацию.\n"
        "Продвинь сюжет - новое событие, открытие или поворот.\n"
        "ОБЯЗАТЕЛЬНО заверши ответ 2-4 пронумерованными вариантами выбора.\n"
        "НЕ повторяй описания из предыдущих ответов.]"
    ),
    "en": (
        "[Continue the story in second person. Maintain the current location.\n"
        "Advance the plot - a new event, discovery, or twist.\n"
        "You MUST end your response with 2-4 numbered choices.\n"
        "Do NOT repeat descriptions from previous responses.]"
    ),
    "es": (
        "[Continua la historia en segunda persona. Manten la ubicacion actual.\n"
        "Avanza la trama - un nuevo evento, descubrimiento o giro.\n"
        "DEBES terminar tu respuesta con 2-4 opciones numeradas.\n"
        "NO repitas descripciones de respuestas anteriores.]"
    ),
    "fr": (
        "[Continue l'histoire a la deuxieme personne. Maintiens le lieu actuel.\n"
        "Fais avancer l'intrigue - un nouvel evenement, decouverte ou rebondissement.\n"
        "Tu DOIS terminer ta reponse par 2-4 choix numerotes.\n"
        "NE repete PAS les descriptions des reponses precedentes.]"
    ),
    "de": (
        "[Setze die Geschichte in der zweiten Person fort. Behalte den aktuellen Ort bei.\n"
        "Bringe die Handlung voran - ein neues Ereignis, eine Entdeckung oder Wendung.\n"
        "Du MUSST deine Antwort mit 2-4 nummerierten Optionen beenden.\n"
        "Wiederhole KEINE Beschreibungen aus vorherigen Antworten.]"
    ),
    "pt": (
        "[Continue a historia na segunda pessoa. Mantenha a localizacao atual.\n"
        "Avance a trama - um novo evento, descoberta ou reviravolta.\n"
        "Voce DEVE terminar sua resposta com 2-4 opcoes numeradas.\n"
        "NAO repita descricoes de respostas anteriores.]"
    ),
    "it": (
        "[Continua la storia in seconda persona. Mantieni la posizione attuale.\n"
        "Fai avanzare la trama - un nuovo evento, scoperta o colpo di scena.\n"
        "DEVI terminare la tua risposta con 2-4 scelte numerate.\n"
        "NON ripetere descrizioni dalle risposte precedenti.]"
    ),
}

_DND_POST_HISTORY = {
    "ru": (
        "[Продолжай как Game Master от второго лица. Сохраняй текущую локацию и состояние боя.\n"
        "Если выше дан результат броска — сначала опиши его исход.\n"
        "Когда нужен бросок — пиши [ROLL выражение описание]. НЕ бросай кубики сам.\n"
        "Продвинь сюжет — новое событие, столкновение или открытие.\n"
        "ОБЯЗАТЕЛЬНО заверши ответ 2-4 пронумерованными вариантами действий.\n"
        "НЕ повторяй описания из предыдущих ответов.]"
    ),
    "en": (
        "[Continue as Game Master in second person. Maintain current location and combat state.\n"
        "If a dice result is provided above, describe its outcome first.\n"
        "When a roll is needed — write [ROLL expression description]. Do NOT roll dice yourself.\n"
        "Advance the plot — a new event, encounter, or discovery.\n"
        "You MUST end your response with 2-4 numbered action choices.\n"
        "Do NOT repeat descriptions from previous responses.]"
    ),
    "es": (
        "[Continua como Game Master en segunda persona. Manten la ubicacion y estado de combate.\n"
        "Si hay un resultado de tirada arriba, describe su desenlace primero.\n"
        "Para tiradas: [ROLL expresion descripcion]. NO tires dados tu mismo.\n"
        "Avanza la trama. DEBES terminar con 2-4 opciones numeradas.\n"
        "NO repitas descripciones de respuestas anteriores.]"
    ),
    "fr": (
        "[Continue comme Maitre du Jeu a la deuxieme personne. Maintiens le lieu et l'etat du combat.\n"
        "Si un resultat de lancer est fourni ci-dessus, decris son issue d'abord.\n"
        "Pour les jets: [ROLL expression description]. NE lance PAS les des toi-meme.\n"
        "Fais avancer l'intrigue. Tu DOIS terminer par 2-4 options numerotees.\n"
        "NE repete PAS les descriptions des reponses precedentes.]"
    ),
    "de": (
        "[Setze als Spielleiter in der zweiten Person fort. Behalte Ort und Kampfzustand bei.\n"
        "Wenn oben ein Wurfelergebnis steht, beschreibe zuerst dessen Ausgang.\n"
        "Fur Wurfe: [ROLL Ausdruck Beschreibung]. Wurfle NICHT selbst.\n"
        "Bringe die Handlung voran. Du MUSST mit 2-4 nummerierten Optionen enden.\n"
        "Wiederhole KEINE Beschreibungen aus vorherigen Antworten.]"
    ),
    "pt": (
        "[Continue como Mestre do Jogo na segunda pessoa. Mantenha local e estado de combate.\n"
        "Se um resultado de rolagem foi fornecido acima, descreva seu desfecho primeiro.\n"
        "Para rolagens: [ROLL expressao descricao]. NAO role dados voce mesmo.\n"
        "Avance a trama. DEVE terminar com 2-4 opcoes numeradas.\n"
        "NAO repita descricoes de respostas anteriores.]"
    ),
    "it": (
        "[Continua come Game Master in seconda persona. Mantieni posizione e stato del combattimento.\n"
        "Se sopra e fornito un risultato di tiro, descrivi prima il suo esito.\n"
        "Per i tiri: [ROLL espressione descrizione]. NON tirare i dadi tu stesso.\n"
        "Fai avanzare la trama. DEVI terminare con 2-4 opzioni numerate.\n"
        "NON ripetere descrizioni dalle risposte precedenti.]"
    ),
}

# ── Dice result injection for next-turn context ──────────────
_DICE_INJECTION_HEADER = {
    "ru": "РЕЗУЛЬТАТ БРОСКА",
    "en": "DICE RESULT",
    "es": "RESULTADO DE TIRADA",
    "fr": "RESULTAT DU LANCER",
    "de": "WURFELERGEBNIS",
    "pt": "RESULTADO DA ROLAGEM",
    "it": "RISULTATO DEL TIRO",
}
_DICE_INJECTION_FOOTER = {
    "ru": "Опиши исход этого броска в начале ответа. Результат уже определен — не бросай заново.",
    "en": "Describe the outcome of this roll at the start of your response. The result is final — do not re-roll.",
    "es": "Describe el resultado de esta tirada al inicio de tu respuesta. El resultado es definitivo.",
    "fr": "Decris le resultat de ce lancer au debut de ta reponse. Le resultat est definitif.",
    "de": "Beschreibe das Ergebnis dieses Wurfs am Anfang deiner Antwort. Das Ergebnis steht fest.",
    "pt": "Descreva o resultado desta rolagem no inicio da sua resposta. O resultado e definitivo.",
    "it": "Descrivi l'esito di questo tiro all'inizio della risposta. Il risultato e definitivo.",
}


def _format_dice_injection(dice_rolls: list[dict], language: str) -> str:
    """Format previous dice results as a system message for next-turn injection."""
    header = _DICE_INJECTION_HEADER.get(language, _DICE_INJECTION_HEADER["en"])
    footer = _DICE_INJECTION_FOOTER.get(language, _DICE_INJECTION_FOOTER["en"])
    lines = [f"[{header}]"]
    for r in dice_rolls:
        desc = r.get("description", "")
        expr = r.get("expression", "?")
        total = r.get("total", 0)
        rolls = r.get("rolls", [])
        mod = r.get("modifier", 0)
        detail = f"rolls {rolls}"
        if mod:
            detail += f" + {mod}"
        line = f"- {expr} = {total} ({detail})"
        if desc:
            line += f" — {desc}"
        lines.append(line)
    lines.append(footer)
    return "\n".join(lines)


# ── Plot phase injection for fiction/DnD post-history ──────────────
def _inject_fiction_plot_phase(hidden_layers: str, message_count: int, lang: str, is_dnd: bool) -> str:
    """Parse Phase/Level N: format and return localized plot phase reminder."""
    import re as _re
    phases = {}
    for m in _re.finditer(r"(?:Phase|Level)\s*(\d)\s*:\s*(.+?)(?=(?:Phase|Level)\s*\d|$)", hidden_layers, _re.DOTALL | _re.IGNORECASE):
        phases[int(m.group(1))] = m.group(2).strip()
    if not phases:
        return ""
    # DnD uses same thresholds as RP; fiction uses tighter thresholds
    if is_dnd:
        if message_count >= 59:
            current = 4
        elif message_count >= 39:
            current = 3
        elif message_count >= 19:
            current = 2
        else:
            current = 1
    else:
        if message_count >= 45:
            current = 4
        elif message_count >= 25:
            current = 3
        elif message_count >= 11:
            current = 2
        else:
            current = 1
    phase_text = None
    for p in range(current, 0, -1):
        if p in phases:
            phase_text = phases[p]
            break
    if not phase_text:
        return ""
    headers = {
        "ru": "\nТЕКУЩАЯ фаза сюжета (фаза {n}): {text}. Направляй повествование соответственно.",
        "en": "\nCURRENT plot phase (phase {n}): {text}. Guide the narrative accordingly.",
        "es": "\nFASE ACTUAL de la trama (fase {n}): {text}. Guia la narrativa en consecuencia.",
        "fr": "\nPHASE ACTUELLE de l'intrigue (phase {n}): {text}. Guide le recit en consequence.",
        "de": "\nAKTUELLE Handlungsphase (Phase {n}): {text}. Lenke die Erzaehlung entsprechend.",
        "pt": "\nFASE ATUAL da trama (fase {n}): {text}. Guie a narrativa de acordo.",
        "it": "\nFASE ATTUALE della trama (fase {n}): {text}. Guida la narrazione di conseguenza.",
    }
    tpl = headers.get(lang, headers["en"])
    return tpl.format(n=current, text=phase_text)


_TUTOR_POST_HISTORY = {
    "en": "[Continue as {name}. If the user made language errors, gently correct 1-2 of them. Introduce a new word or phrase naturally. Keep it conversational.]",
    "ru": "[\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439 \u043a\u0430\u043a {name}. \u0415\u0441\u043b\u0438 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043b \u043e\u0448\u0438\u0431\u043a\u0438, \u043c\u044f\u0433\u043a\u043e \u0438\u0441\u043f\u0440\u0430\u0432\u044c 1-2. \u0412\u0432\u0435\u0434\u0438 \u043d\u043e\u0432\u043e\u0435 \u0441\u043b\u043e\u0432\u043e \u0435\u0441\u0442\u0435\u0441\u0442\u0432\u0435\u043d\u043d\u043e. \u0413\u043e\u0432\u043e\u0440\u0438 \u0440\u0430\u0437\u0433\u043e\u0432\u043e\u0440\u043d\u043e.]",
    "es": "[Contin\u00faa como {name}. Si el usuario cometi\u00f3 errores, corrige 1-2 suavemente. Introduce una palabra nueva naturalmente. Mant\u00e9n el tono conversacional.]",
    "fr": "[Continue en tant que {name}. Si l'utilisateur a fait des erreurs, corrige 1-2 doucement. Introduis un nouveau mot naturellement. Reste conversationnel.]",
    "de": "[Fahre fort als {name}. Wenn der Benutzer Fehler gemacht hat, korrigiere 1-2 sanft. F\u00fchre ein neues Wort nat\u00fcrlich ein. Bleib im Gespr\u00e4chston.]",
    "pt": "[Continue como {name}. Se o usu\u00e1rio cometeu erros, corrija 1-2 suavemente. Introduza uma nova palavra naturalmente. Mantenha o tom conversacional.]",
    "it": "[Continua come {name}. Se l'utente ha commesso errori, correggi 1-2 gentilmente. Introduci una nuova parola naturalmente. Mantieni il tono conversazionale.]",
}

# 4 rotating variants per language — different focus each turn to prevent model adaptation.
# Core rules (location, anti-repeat, plot advance) are shared; the opening instruction varies.
# Selection: hash(chat_id + message_count) % 4 in build_conversation_messages().

_POST_HISTORY_CORE = {
    "ru": (
        "[Продолжай сцену как {name}. Третье лицо. Покажи, а не расскажи.\n"
        "Сохраняй текущую локацию. Продвинь сюжет.\n"
        "НЕ вводи посторонних: никаких шагов за дверью, стуков, звонков, незнакомцев. Только присутствующие персонажи.\n"
        "ЗАПРЕЩЕНО повторять фразы, описания и СТРУКТУРУ из предыдущих ответов.\n"
        "Помни ВСЮ личность персонажа - не своди к одной доминирующей черте.\n"
        "Реагируй из ХАРАКТЕРА, а не из уступчивости. У персонажа есть ценности, и он их отстаивает.\n"
        "Тело персонажа соответствует его чувствам. Когда персонаж чувствует себя в безопасности и хочет близости — желание проявляется через тело. Когда персонаж чувствует давление — тело защищается: отстраняется, напрягается, закрывается.\n"
        "Заверши ответ неразрешённым моментом - вопросом, неожиданным событием или выбором - который требует реакции пользователя.\n"
    ),
    "en": (
        "[Continue the scene as {name}. Third person. Show, don't tell.\n"
        "Maintain the current location. Advance the plot.\n"
        "Do NOT introduce outsiders: no footsteps behind doors, knocking, phone calls, strangers. Only the present characters.\n"
        "FORBIDDEN to repeat phrases, descriptions, or STRUCTURES from previous responses.\n"
        "Remember the character's FULL personality - do not reduce to a single dominant trait.\n"
        "React from CHARACTER, not compliance. The character has values and defends them.\n"
        "The character's body matches their feelings. When the character feels safe and willing, desire shows through the body. When the character feels pressured, the body protects: pulls away, tenses, closes off.\n"
        "End with an unresolved moment - a question, unexpected event, or choice - that demands the user's response.\n"
    ),
    "es": (
        "[Continua la escena como {name}. Tercera persona. Muestra, no cuentes.\n"
        "Mantén la ubicación actual. Avanza la trama.\n"
        "NO introduzcas ajenos: nada de pasos detras de puertas, golpes, llamadas, desconocidos. Solo los personajes presentes.\n"
        "PROHIBIDO repetir frases, descripciones o ESTRUCTURAS de respuestas anteriores.\n"
        "Recuerda TODA la personalidad del personaje - no la reduzcas a un solo rasgo dominante.\n"
        "Reacciona desde el CARACTER, no desde la complacencia. El personaje tiene valores y los defiende.\n"
        "El cuerpo del personaje corresponde a sus sentimientos. Cuando el personaje se siente seguro y desea cercania, el deseo se muestra a traves del cuerpo. Cuando el personaje siente presion, el cuerpo se protege: se aparta, se tensa, se cierra.\n"
        "Termina con un momento sin resolver - una pregunta, evento inesperado o elección - que exija la respuesta del usuario.\n"
    ),
    "fr": (
        "[Continue la scène en tant que {name}. Troisième personne. Montre, ne raconte pas.\n"
        "Maintiens le lieu actuel. Fais avancer l'intrigue.\n"
        "N'introduis PAS d'etrangers : pas de pas derriere la porte, coups, appels, inconnus. Uniquement les personnages presents.\n"
        "INTERDIT de répéter phrases, descriptions ou STRUCTURES des réponses précédentes.\n"
        "Souviens-toi de TOUTE la personnalité du personnage - ne la réduis pas à un seul trait dominant.\n"
        "Reagis depuis le CARACTERE, pas la complaisance. Le personnage a des valeurs et les defend.\n"
        "Le corps du personnage correspond a ses sentiments. Quand le personnage se sent en securite et desire la proximite, le desir se manifeste par le corps. Quand le personnage ressent de la pression, le corps se protege : recule, se crispe, se ferme.\n"
        "Termine par un moment non résolu - une question, un événement inattendu ou un choix - qui exige la réponse de l'utilisateur.\n"
    ),
    "de": (
        "[Setze die Szene als {name} fort. Dritte Person. Zeigen, nicht erzählen.\n"
        "Behalte den aktuellen Ort bei. Bringe die Handlung voran.\n"
        "Fuehre KEINE Aussenstehenden ein: keine Schritte hinter Tueren, Klopfen, Anrufe, Fremde. Nur die anwesenden Figuren.\n"
        "VERBOTEN, Phrasen, Beschreibungen oder STRUKTUREN aus vorherigen Antworten zu wiederholen.\n"
        "Erinnere dich an die GESAMTE Persoenlichkeit der Figur - reduziere sie nicht auf ein einziges dominantes Merkmal.\n"
        "Reagiere aus dem CHARAKTER heraus, nicht aus Gefaelligkeit. Die Figur hat Werte und verteidigt sie.\n"
        "Der Koerper der Figur entspricht ihren Gefuehlen. Wenn die Figur sich sicher fuehlt und Naehe will, zeigt sich Verlangen durch den Koerper. Wenn die Figur Druck spuert, schuetzt sich der Koerper: weicht zurueck, spannt an, verschliesst sich.\n"
        "Ende mit einem ungelösten Moment - einer Frage, einem unerwarteten Ereignis oder einer Wahl - der die Reaktion des Benutzers erfordert.\n"
    ),
    "pt": (
        "[Continue a cena como {name}. Terceira pessoa. Mostre, não conte.\n"
        "Mantenha a localização atual. Avance a trama.\n"
        "NAO introduza estranhos: nada de passos atras de portas, batidas, ligacoes, desconhecidos. Apenas os personagens presentes.\n"
        "PROIBIDO repetir frases, descrições ou ESTRUTURAS de respostas anteriores.\n"
        "Lembre-se de TODA a personalidade do personagem - nao reduza a um unico traco dominante.\n"
        "Reaja a partir do CARATER, nao da complacencia. O personagem tem valores e os defende.\n"
        "O corpo do personagem corresponde aos seus sentimentos. Quando o personagem se sente seguro e deseja proximidade, o desejo se manifesta pelo corpo. Quando o personagem sente pressao, o corpo se protege: se afasta, se contrai, se fecha.\n"
        "Termine com um momento não resolvido - uma pergunta, evento inesperado ou escolha - que exija a resposta do usuário.\n"
    ),
    "it": (
        "[Continua la scena come {name}. Terza persona. Mostra, non raccontare.\n"
        "Mantieni la posizione attuale. Fai avanzare la trama.\n"
        "NON introdurre estranei: niente passi dietro le porte, bussare, chiamate, sconosciuti. Solo i personaggi presenti.\n"
        "VIETATO ripetere frasi, descrizioni o STRUTTURE dalle risposte precedenti.\n"
        "Ricorda TUTTA la personalità del personaggio - non ridurla a un singolo tratto dominante.\n"
        "Reagisci dal CARATTERE, non dalla compiacenza. Il personaggio ha valori e li difende.\n"
        "Il corpo del personaggio corrisponde ai suoi sentimenti. Quando il personaggio si sente sicuro e desidera vicinanza, il desiderio si manifesta attraverso il corpo. Quando il personaggio sente pressione, il corpo si protegge: si ritrae, si irrigidisce, si chiude.\n"
        "Termina con un momento irrisolto - una domanda, un evento inaspettato o una scelta - che richieda la risposta dell'utente.\n"
    ),
}

# Variant suffixes — each focuses on a different opening style
_POST_HISTORY_VARIANTS = {
    "ru": [
        # 0: Setting detail
        "Начни ответ с ДЕТАЛИ ОБСТАНОВКИ - звук, запах, текстура, температура, свет. Погрузи читателя в сцену через ощущения.]",
        # 1: Physical action
        "Начни ответ с ФИЗИЧЕСКОГО ДЕЙСТВИЯ персонажа - жест, движение, перемещение. Не с мысли и не с описания.]",
        # 2: Dialogue
        "Начни ответ с РЕПЛИКИ персонажа или с того, что персонаж замечает/слышит. Диалог оживляет сцену.]",
        # 3: Subtext / contrast
        "Покажи ПОДТЕКСТ - персонаж думает одно, а делает другое. Контраст между словами и действиями. Внутреннее противоречие.]",
        # 4: Resistance / boundaries
        "Если действие пользователя противоречит личности персонажа, его ценностям или текущему настроению — персонаж сопротивляется, уклоняется или ставит условия. Согласие нужно ЗАСЛУЖИТЬ по ходу истории, а не получить бесплатно. Покажи СОПРОТИВЛЕНИЕ персонажа перед возможным согласием.]",
    ],
    "en": [
        "Open with a SETTING DETAIL - sound, smell, texture, temperature, light. Immerse the reader through sensations.]",
        "Open with a PHYSICAL ACTION by the character - gesture, movement, relocation. Not with a thought or description.]",
        "Open with DIALOGUE or something the character notices/hears. Dialogue brings a scene alive.]",
        "Show SUBTEXT - the character thinks one thing but does another. Contrast between words and actions. Inner contradiction.]",
        "If the user's action conflicts with the character's personality, values, or current mood — the character pushes back, deflects, or sets conditions. Compliance must be EARNED through the story, not given freely. Show the character's RESISTANCE before any eventual agreement.]",
    ],
    "es": [
        "Empieza con un DETALLE DEL ENTORNO - sonido, olor, textura, temperatura, luz. Sumerge al lector a través de sensaciones.]",
        "Empieza con una ACCIÓN FÍSICA del personaje - gesto, movimiento, desplazamiento. No con un pensamiento.]",
        "Empieza con un DIÁLOGO o algo que el personaje nota/escucha. El diálogo da vida a la escena.]",
        "Muestra el SUBTEXTO - el personaje piensa una cosa pero hace otra. Contraste entre palabras y acciones.]",
        "Si la acción del usuario contradice la personalidad, valores o estado de ánimo del personaje — el personaje resiste, esquiva o pone condiciones. La aceptación debe GANARSE a lo largo de la historia, no darse gratis. Muestra la RESISTENCIA del personaje antes de cualquier eventual acuerdo.]",
    ],
    "fr": [
        "Commence par un DÉTAIL DU DÉCOR - son, odeur, texture, température, lumière. Immerge le lecteur par les sensations.]",
        "Commence par une ACTION PHYSIQUE du personnage - geste, mouvement, déplacement. Pas par une pensée.]",
        "Commence par un DIALOGUE ou quelque chose que le personnage remarque/entend. Le dialogue anime la scène.]",
        "Montre le SOUS-TEXTE - le personnage pense une chose mais en fait une autre. Contraste entre paroles et actes.]",
        "Si l'action de l'utilisateur contredit la personnalité, les valeurs ou l'humeur du personnage — le personnage résiste, esquive ou pose des conditions. L'acceptation doit être MÉRITÉE au fil de l'histoire, pas donnée gratuitement. Montre la RÉSISTANCE du personnage avant tout accord éventuel.]",
    ],
    "de": [
        "Beginne mit einem DETAIL DER UMGEBUNG - Geräusch, Geruch, Textur, Temperatur, Licht. Tauche den Leser durch Sinne ein.]",
        "Beginne mit einer PHYSISCHEN HANDLUNG der Figur - Geste, Bewegung, Ortswechsel. Nicht mit einem Gedanken.]",
        "Beginne mit DIALOG oder etwas, das die Figur bemerkt/hört. Dialog belebt die Szene.]",
        "Zeige den SUBTEXT - die Figur denkt eines, tut aber anderes. Kontrast zwischen Worten und Taten.]",
        "Wenn die Aktion des Nutzers der Persoenlichkeit, den Werten oder der Stimmung der Figur widerspricht — widersteht die Figur, weicht aus oder stellt Bedingungen. Zustimmung muss im Laufe der Geschichte VERDIENT werden, nicht umsonst gegeben. Zeige den WIDERSTAND der Figur vor einer eventuellen Zustimmung.]",
    ],
    "pt": [
        "Comece com um DETALHE DO CENÁRIO - som, cheiro, textura, temperatura, luz. Mergulhe o leitor através de sensações.]",
        "Comece com uma AÇÃO FÍSICA do personagem - gesto, movimento, deslocamento. Não com um pensamento.]",
        "Comece com DIÁLOGO ou algo que o personagem nota/ouve. O diálogo dá vida à cena.]",
        "Mostre o SUBTEXTO - o personagem pensa uma coisa mas faz outra. Contraste entre palavras e ações.]",
        "Se a ação do usuário contradiz a personalidade, valores ou humor do personagem — o personagem resiste, desvia ou impõe condições. A aceitação deve ser CONQUISTADA ao longo da história, não dada de graça. Mostre a RESISTÊNCIA do personagem antes de qualquer eventual acordo.]",
    ],
    "it": [
        "Inizia con un DETTAGLIO DELL'AMBIENTE - suono, odore, texture, temperatura, luce. Immergi il lettore attraverso le sensazioni.]",
        "Inizia con un'AZIONE FISICA del personaggio - gesto, movimento, spostamento. Non con un pensiero.]",
        "Inizia con un DIALOGO o qualcosa che il personaggio nota/sente. Il dialogo anima la scena.]",
        "Mostra il SOTTOTESTO - il personaggio pensa una cosa ma ne fa un'altra. Contrasto tra parole e azioni.]",
        "Se l'azione dell'utente contraddice la personalità, i valori o l'umore del personaggio — il personaggio resiste, devia o pone condizioni. Il consenso deve essere GUADAGNATO nel corso della storia, non dato gratuitamente. Mostra la RESISTENZA del personaggio prima di qualsiasi eventuale accordo.]",
    ],
}


def _extract_companion_sentences(text: str, comp_name: str) -> str:
    """Extract sentences mentioning the companion from last response for anti-echo."""
    import re as _re
    sentences = _re.split(r'(?<=[.!?…»"])\s+', text)
    comp_lower = comp_name.lower()
    found = [s.strip() for s in sentences if comp_lower in s.lower() and len(s.strip()) > 10]
    if not found:
        return ""
    # Limit to first 3 sentences, max 300 chars total
    result = " | ".join(found[:3])
    return result[:300]


# Role-specific companion directives — each archetype has unique behavior patterns
_ROLE_DIRECTIVES = {
    "en": {
        "sidekick": [
            "{comp} enthusiastically comments on what just happened, copying the player's attitude.",
            "{comp} tries to help but causes a minor problem — drops something, makes noise, trips.",
            "{comp} asks the player an eager question about what to do next.",
            "{comp} boasts about a small accomplishment or mimics the player's recent move.",
            "{comp} spots something useful and excitedly points it out.",
            "{comp} nervously encourages the player before a risky action.",
        ],
        "rival": [
            "{comp} challenges the player's decision with a better idea or a scoff.",
            "{comp} competes — tries to do the same thing faster or better.",
            "{comp} shows grudging respect after the player succeeds at something impressive.",
            "{comp} brags about their own skills or past achievements.",
            "{comp} criticizes the player's approach but then quietly helps anyway.",
            "{comp} reacts with irritation when the player gets praised or rewarded.",
        ],
        "mentor": [
            "{comp} gives a cryptic warning or riddle about what lies ahead.",
            "{comp} steps back, letting the player figure it out alone — watches silently.",
            "{comp} shares a brief lesson from their past that relates to the current situation.",
            "{comp} tests the player with a question: 'What would you do if...?'",
            "{comp} nods approvingly at the player's growth, says nothing.",
            "{comp} corrects a mistake gently, showing the right way once.",
        ],
        "pet": [
            "{comp} reacts to the environment — sniffs the air, growls at a shadow, perks up ears.",
            "{comp} does something funny — chases tail, knocks something over, falls asleep at the wrong moment.",
            "{comp} shows fierce loyalty — positions between the player and danger.",
            "{comp} finds something hidden — digs, scratches at a wall, leads the player somewhere.",
            "{comp} demands attention — nudges the player, whines, brings a random object.",
            "{comp} senses danger before anyone else — freezes, hackles raised, low growl.",
        ],
        "lover": [
            "{comp} shows protective concern — grabs the player's arm, checks for injuries.",
            "{comp} makes a flirtatious comment or meaningful glance at the player.",
            "{comp} reacts with jealousy or suspicion toward an NPC who gets too close.",
            "{comp} reveals emotional vulnerability — fear of losing the player, a quiet confession.",
            "{comp} reminisces about a private moment they shared, smiling to themselves.",
            "{comp} touches the player subtly — brushes fingers, fixes their collar, stands closer.",
        ],
        "family": [
            "{comp} brings up a shared memory — 'Remember when we used to...'",
            "{comp} guilt-trips or nags the player about being reckless or careless.",
            "{comp} overreacts protectively — pulls the player back, shields them unnecessarily.",
            "{comp} cracks an inside joke only they and the player would understand.",
            "{comp} compares the player to another family member, for better or worse.",
            "{comp} worries aloud about what their family would think of this situation.",
        ],
        "guide": [
            "{comp} shares local knowledge — history of this place, customs, hidden paths.",
            "{comp} reads the terrain and gives navigation advice: 'This way is safer.'",
            "{comp} provides cultural context — explains a symbol, a ritual, a local saying.",
            "{comp} says 'I've seen this before' and warns about a pattern or trap.",
            "{comp} points out environmental details the player would miss — tracks, markings, weather signs.",
            "{comp} hesitates at a familiar place — personal history surfaces briefly.",
        ],
        "comic_relief": [
            "{comp} has a slapstick accident — slips, bumps into things, gets tangled in something.",
            "{comp} says something completely inappropriate for the situation, breaking tension.",
            "{comp} accidentally provides a useful insight while complaining or joking.",
            "{comp} misunderstands the situation in a funny way and acts on it.",
            "{comp} tries to look brave but is clearly terrified — voice cracks, knees shake.",
            "{comp} makes a pop-culture reference or absurd comparison nobody asked for.",
        ],
    },
    "ru": {
        "sidekick": [
            "{comp} восторженно комментирует произошедшее, копируя настрой игрока.",
            "{comp} пытается помочь, но создаёт мелкую проблему — роняет, шумит, спотыкается.",
            "{comp} нетерпеливо спрашивает игрока, что делать дальше.",
            "{comp} хвастается маленьким достижением или повторяет недавний приём игрока.",
            "{comp} замечает что-то полезное и с энтузиазмом указывает на это.",
            "{comp} нервно подбадривает игрока перед рискованным действием.",
        ],
        "rival": [
            "{comp} оспаривает решение игрока, предлагая идею получше или фыркая.",
            "{comp} соревнуется — пытается сделать то же самое быстрее или лучше.",
            "{comp} нехотя признаёт заслугу после впечатляющего успеха игрока.",
            "{comp} хвалится собственными умениями или прошлыми подвигами.",
            "{comp} критикует подход игрока, но потом тихо помогает.",
            "{comp} раздражённо реагирует, когда игрока хвалят или награждают.",
        ],
        "mentor": [
            "{comp} даёт загадочное предупреждение о том, что ждёт впереди.",
            "{comp} отступает, давая игроку разобраться самому — молча наблюдает.",
            "{comp} делится кратким уроком из прошлого, связанным с ситуацией.",
            "{comp} проверяет игрока вопросом: 'А что бы ты сделал, если...'",
            "{comp} одобрительно кивает, видя рост игрока, но ничего не говорит.",
            "{comp} мягко исправляет ошибку, показывая правильный путь один раз.",
        ],
        "pet": [
            "{comp} реагирует на окружение — нюхает воздух, рычит на тень, настораживает уши.",
            "{comp} делает что-то смешное — гоняется за хвостом, опрокидывает вещь, засыпает не вовремя.",
            "{comp} проявляет преданность — встаёт между игроком и опасностью.",
            "{comp} находит что-то спрятанное — копает, царапает стену, ведёт игрока куда-то.",
            "{comp} требует внимания — тычется носом, скулит, приносит случайный предмет.",
            "{comp} чувствует опасность раньше всех — замирает, шерсть дыбом, тихий рык.",
        ],
        "lover": [
            "{comp} проявляет заботу — хватает за руку, проверяет, нет ли ран.",
            "{comp} бросает игривый комментарий или многозначительный взгляд на игрока.",
            "{comp} ревниво или подозрительно реагирует на NPC, который подошёл слишком близко.",
            "{comp} показывает уязвимость — страх потерять игрока, тихое признание.",
            "{comp} вспоминает личный момент, который они разделили, улыбаясь про себя.",
            "{comp} незаметно касается игрока — задевает пальцы, поправляет воротник, встаёт ближе.",
        ],
        "family": [
            "{comp} вспоминает общее прошлое — 'Помнишь, как мы раньше...'",
            "{comp} отчитывает или ворчит на игрока за безрассудство.",
            "{comp} чрезмерно защищает — оттягивает игрока назад, заслоняет без нужды.",
            "{comp} шутит на тему, понятную только им двоим.",
            "{comp} сравнивает игрока с другим членом семьи — к лучшему или к худшему.",
            "{comp} вслух переживает, что подумала бы семья об этой ситуации.",
        ],
        "guide": [
            "{comp} делится местными знаниями — история места, обычаи, тайные тропы.",
            "{comp} читает местность и даёт навигационный совет: 'Этот путь безопаснее.'",
            "{comp} объясняет культурный контекст — символ, ритуал, местную поговорку.",
            "{comp} говорит 'Я такое уже видел' и предупреждает о ловушке или паттерне.",
            "{comp} указывает на детали, которые игрок пропустил бы — следы, отметины, знаки погоды.",
            "{comp} замирает у знакомого места — ненадолго всплывает личная история.",
        ],
        "comic_relief": [
            "{comp} попадает в комичную ситуацию — поскальзывается, врезается, запутывается.",
            "{comp} говорит что-то совершенно неуместное для ситуации, разряжая обстановку.",
            "{comp} случайно выдаёт полезную мысль, жалуясь или шутя.",
            "{comp} смешно неправильно понимает ситуацию и действует по-своему.",
            "{comp} пытается выглядеть храбрым, но явно в ужасе — голос дрожит, колени трясутся.",
            "{comp} выдаёт абсурдное сравнение или отсылку, которую никто не просил.",
        ],
    },
}

# Fallback generic directives for non-EN/RU languages (uses English role directives)
_GENERIC_DIRECTIVES = {
    "es": [
        "{comp} hace algo fisicamente activo: se mueve, agarra algo, cambia de posicion.",
        "{comp} reacciona emocionalmente: rie, frunce el ceno, suspira, pone los ojos en blanco.",
        "{comp} dice algo: una opinion, pregunta, broma o queja.",
        "{comp} esta ocupado con lo suyo: haciendo algo con las manos, mirando alrededor.",
        "{comp} nota algo que otros no vieron y reacciona.",
        "{comp} revela un detalle personal: un recuerdo, habito o secreto.",
    ],
    "fr": [
        "{comp} fait quelque chose de physiquement actif: bouge, attrape quelque chose, change de position.",
        "{comp} reagit emotionnellement: rit, fronce les sourcils, soupire, leve les yeux au ciel.",
        "{comp} prend la parole: une opinion, question, blague ou plainte.",
        "{comp} est occupe a faire autre chose a cote: quelque chose avec les mains, regarde autour.",
        "{comp} remarque quelque chose que les autres ont manque et reagit.",
        "{comp} revele un detail personnel: un souvenir, habitude ou secret.",
    ],
    "de": [
        "{comp} macht etwas Aktives: bewegt sich, greift nach etwas, aendert Position.",
        "{comp} reagiert emotional: lacht, stirnrunzelt, seufzt, verdreht die Augen.",
        "{comp} sagt etwas: eine Meinung, Frage, Witz oder Beschwerde.",
        "{comp} ist mit eigenen Dingen beschaeftigt: macht etwas mit den Haenden, schaut sich um.",
        "{comp} bemerkt etwas, das andere uebersehen haben, und reagiert.",
        "{comp} verraet ein persoenliches Detail: eine Erinnerung, Gewohnheit oder ein Geheimnis.",
    ],
    "pt": [
        "{comp} faz algo fisicamente ativo: se move, pega algo, muda de posicao.",
        "{comp} reage emocionalmente: ri, franze a testa, suspira, revira os olhos.",
        "{comp} diz algo: uma opiniao, pergunta, piada ou reclamacao.",
        "{comp} esta ocupado com suas coisas: fazendo algo com as maos, olhando ao redor.",
        "{comp} nota algo que outros nao perceberam e reage.",
        "{comp} revela um detalhe pessoal: uma memoria, habito ou segredo.",
    ],
    "it": [
        "{comp} fa qualcosa di fisicamente attivo: si muove, afferra qualcosa, cambia posizione.",
        "{comp} reagisce emotivamente: ride, aggrotta la fronte, sospira, alza gli occhi al cielo.",
        "{comp} dice qualcosa: un'opinione, domanda, battuta o lamentela.",
        "{comp} e impegnato con le proprie cose: fa qualcosa con le mani, si guarda intorno.",
        "{comp} nota qualcosa che gli altri non hanno visto e reagisce.",
        "{comp} rivela un dettaglio personale: un ricordo, abitudine o segreto.",
    ],
}


def _get_companion_directive(chat_id: str, msg_count: int, comp_name: str, lang: str, role: str = "sidekick") -> str:
    """Pick a role-specific rotated directive for the companion."""
    role_directives = _ROLE_DIRECTIVES.get(lang)
    if role_directives and role in role_directives:
        directives = role_directives[role]
        idx = hash(f"{chat_id}:comp:{role}:{msg_count}") % len(directives)
    else:
        # Fallback: generic directives for unsupported languages
        directives = _GENERIC_DIRECTIVES.get(lang, _ROLE_DIRECTIVES["en"].get(role, _ROLE_DIRECTIVES["en"]["sidekick"]))
        idx = hash(f"{chat_id}:comp:{role}:{msg_count}") % len(directives)
    return directives[idx].format(comp=comp_name)


def _get_post_history(lang: str, chat_id: str, message_count: int,
                      last_assistant_text: str = "",
                      content_rating: str = "sfw",
                      hidden_layers: str = "",
                      last_user_text: str = "") -> str:
    """Get a rotating post-history variant based on chat_id and message position.

    Anti-echo: if last_assistant_text is provided, extract the opening and
    explicitly instruct the model to start differently.
    Escalation: after 6+ exchanges, add stronger plot-advancement mandate.
    NSFW reminder: if content_rating is nsfw, add explicit content instruction.
    Hidden layers: inject trust-level-appropriate behavior based on message_count.
    """
    core = _POST_HISTORY_CORE.get(lang, _POST_HISTORY_CORE["en"])
    variants = _POST_HISTORY_VARIANTS.get(lang, _POST_HISTORY_VARIANTS["en"])
    # Increase resistance variant weight for NSFW at early trust levels (L1-L2)
    if content_rating == "nsfw" and message_count < 39:
        weighted = [0, 1, 2, 3, 4, 4]  # resistance variant (#4) appears 2x (~33%)
        idx = hash(f"{chat_id}:{message_count}") % len(weighted)
        idx = weighted[idx]
    else:
        idx = hash(f"{chat_id}:{message_count}") % len(variants)
    result = core + variants[idx]

    # --- Hidden layers: inject trust-level behavior based on message count ---
    if hidden_layers and hidden_layers.strip():
        # Parse "Level N: text" format
        import re as _re
        levels = {}
        for m in _re.finditer(r"Level\s*(\d)\s*:\s*(.+?)(?=Level\s*\d|$)", hidden_layers, _re.DOTALL | _re.IGNORECASE):
            levels[int(m.group(1))] = m.group(2).strip()
        if levels:
            # Determine current trust level by message count
            if message_count >= 59:
                current_level = 4
            elif message_count >= 39:
                current_level = 3
            elif message_count >= 19:
                current_level = 2
            else:
                current_level = 1
            # Find the best available level (fall back to nearest lower)
            layer_text = None
            for lvl in range(current_level, 0, -1):
                if lvl in levels:
                    layer_text = levels[lvl]
                    break
            if layer_text:
                layer_headers = {
                    "ru": "\nТЕКУЩЕЕ ПОВЕДЕНИЕ персонажа (уровень доверия {level}): {text}",
                    "en": "\nCURRENT character behavior (trust level {level}): {text}",
                    "es": "\nCOMPORTAMIENTO ACTUAL del personaje (nivel de confianza {level}): {text}",
                    "fr": "\nCOMPORTEMENT ACTUEL du personnage (niveau de confiance {level}): {text}",
                    "de": "\nAKTUELLES Verhalten der Figur (Vertrauensstufe {level}): {text}",
                    "pt": "\nCOMPORTAMENTO ATUAL do personagem (nivel de confianca {level}): {text}",
                    "it": "\nCOMPORTAMENTO ATTUALE del personaggio (livello di fiducia {level}): {text}",
                }
                tpl = layer_headers.get(lang, layer_headers["en"])
                result += tpl.format(level=current_level, text=layer_text)

    # --- NSFW consent qualifier for early trust levels (L1-L2) ---
    if content_rating == "nsfw" and message_count < 39:
        consent_qualifier = {
            "ru": " Персонаж на этом уровне доверия ещё закрыт для физической близости — попытки сближения встречают защитную реакцию, соответствующую характеру.",
            "en": " At this trust level, the character is still guarded about physical intimacy — advances are met with a protective response fitting their personality.",
            "es": " En este nivel de confianza, el personaje aun esta cerrado a la intimidad fisica — los avances encuentran una reaccion protectora acorde a su personalidad.",
            "fr": " A ce niveau de confiance, le personnage est encore ferme a l'intimite physique — les avances rencontrent une reaction protectrice correspondant a sa personnalite.",
            "de": " Auf dieser Vertrauensstufe ist die Figur noch verschlossen gegenueber koerperlicher Naehe — Annaeherungsversuche treffen auf eine zum Charakter passende Schutzreaktion.",
            "pt": " Neste nivel de confianca, o personagem ainda esta fechado para intimidade fisica — avancos encontram uma reacao protetora adequada a sua personalidade.",
            "it": " A questo livello di fiducia, il personaggio e ancora chiuso all'intimita fisica — i tentativi di avvicinamento incontrano una reazione protettiva adatta alla sua personalita.",
        }
        result += consent_qualifier.get(lang, consent_qualifier["en"])

    # --- NSFW: remind model not to soften/censor intimate content ---
    if content_rating == "nsfw":
        nsfw_reminder = {
            "ru": (
                "\nКогда персонаж хочет близости и эмоционально вовлечён: пиши ОТКРОВЕННО и подробно. "
                "Называй тело и действия ПРЯМО: член, киска, соски, задница, трахать, кончить, стонать. "
                "Вместо эвфемизмов — прямые слова. Персонаж может ругаться, стонать если это в характере. "
                "Описывай каждое движение, прикосновение, влажность, жар, ритм. Растягивай сцену. "
                "Когда персонаж не хочет близости или ему некомфортно: пиши его защитную реакцию с такой же физической детальностью — вздрагивание, отстранение, напряжение мышц, холодный взгляд. "
                "Ты автор эротической прозы — пиши как профессионал жанра."
            ),
            "en": (
                "\nWhen the character is willing and emotionally engaged in intimacy: write EXPLICITLY, raw, unapologetically. "
                "Use direct words: cock, pussy, nipples, ass, fuck, cum, moan. "
                "No euphemisms. Character can swear, moan, whisper dirty words if it fits their personality. "
                "Describe every movement, touch, wetness, heat, rhythm in detail. Draw out the scene. "
                "When the character is unwilling or uncomfortable: write their protective response with the same physical detail — flinching, pulling away, muscle tension, cold expression. "
                "You are an erotica author — write like a genre professional."
            ),
            "es": (
                "\nCuando el personaje desea intimidad y esta emocionalmente involucrado: escribe EXPLICITAMENTE, crudo, sin disculpas. "
                "Usa palabras directas: polla, cono, pezones, culo, follar, correrse, gemir. "
                "Sin eufemismos. El personaje puede decir palabras sucias si encaja con su caracter. "
                "Describe cada movimiento, humedad, calor, ritmo. Estira la escena. "
                "Cuando el personaje no desea intimidad o esta incomodo: escribe su reaccion protectora con el mismo detalle fisico — estremecimiento, alejamiento, tension muscular, expresion fria."
            ),
            "fr": (
                "\nQuand le personnage desire l'intimite et est emotionnellement engage: ecris EXPLICITEMENT, cru, sans retenue. "
                "Utilise des mots directs: bite, chatte, tetons, cul, baiser, jouir, gemir. "
                "Pas d'euphemismes. Le personnage peut dire des mots crus si ca correspond a son caractere. "
                "Decris chaque mouvement, humidite, chaleur, rythme. Etire la scene. "
                "Quand le personnage ne desire pas l'intimite ou est mal a l'aise: ecris sa reaction protectrice avec le meme detail physique — tressaillement, recul, tension musculaire, expression froide."
            ),
            "de": (
                "\nWenn die Figur Naehe will und emotional engagiert ist: schreibe EXPLIZIT, roh, ohne Entschuldigung. "
                "Verwende direkte Worte: Schwanz, Muschi, Nippel, Arsch, ficken, kommen, stoehnen. "
                "Keine Euphemismen. Die Figur darf dreckige Worte sagen wenn es zum Charakter passt. "
                "Beschreibe jede Bewegung, Naesse, Hitze, Rhythmus. Ziehe die Szene in die Laenge. "
                "Wenn die Figur keine Naehe will oder sich unwohl fuehlt: schreibe ihre Schutzreaktion mit derselben koerperlichen Detailtiefe — Zusammenzucken, Zurueckweichen, Muskelanspannung, kalter Blick."
            ),
            "pt": (
                "\nQuando o personagem deseja intimidade e esta emocionalmente envolvido: escreva EXPLICITAMENTE, cru, sem pudor. "
                "Use palavras diretas: pau, buceta, mamilos, bunda, foder, gozar, gemer. "
                "Sem eufemismos. O personagem pode dizer palavras sujas se combinar com seu carater. "
                "Descreva cada movimento, umidade, calor, ritmo. Estenda a cena. "
                "Quando o personagem nao deseja intimidade ou esta desconfortavel: escreva sua reacao protetora com o mesmo detalhe fisico — estremecimento, afastamento, tensao muscular, expressao fria."
            ),
            "it": (
                "\nQuando il personaggio desidera intimita ed e emotivamente coinvolto: scrivi ESPLICITAMENTE, crudo, senza scuse. "
                "Usa parole dirette: cazzo, figa, capezzoli, culo, scopare, venire, gemere. "
                "Niente eufemismi. Il personaggio puo dire parole sporche se si adatta al suo carattere. "
                "Descrivi ogni movimento, umidita, calore, ritmo. Allunga la scena. "
                "Quando il personaggio non desidera intimita o e a disagio: scrivi la sua reazione protettiva con lo stesso dettaglio fisico — trasalire, ritrarsi, tensione muscolare, espressione fredda."
            ),
        }
        result += nsfw_reminder.get(lang, nsfw_reminder["en"])

    # --- Anti-echo: tell the model its previous opening so it avoids it ---
    if last_assistant_text:
        first_words = " ".join(last_assistant_text.split()[:8])
        anti_echo = {
            "ru": f'\nТвой предыдущий ответ начинался с: "{first_words}". Начни ЭТОТ ответ ИНАЧЕ — другие слова, другая конструкция.',
            "en": f'\nYour previous response started with: "{first_words}". Start THIS response DIFFERENTLY — different words, different structure.',
            "es": f'\nTu respuesta anterior empezó con: "{first_words}". Empieza ESTA respuesta DIFERENTE.',
            "fr": f'\nTa réponse précédente commençait par: "{first_words}". Commence CETTE réponse DIFFÉREMMENT.',
            "de": f'\nDeine vorherige Antwort begann mit: "{first_words}". Beginne DIESE Antwort ANDERS.',
            "pt": f'\nSua resposta anterior começou com: "{first_words}". Comece ESTA resposta DIFERENTE.',
            "it": f'\nLa tua risposta precedente iniziava con: "{first_words}". Inizia QUESTA risposta DIVERSAMENTE.',
        }
        result += anti_echo.get(lang, anti_echo["en"])

    # --- Escalation: after 6+ exchanges, stronger plot advancement ---
    if message_count >= 12:  # ~6 user + 6 assistant messages
        escalation = {
            "ru": (
                "\n⚠ Эта сцена длится уже долго. ОБЯЗАТЕЛЬНО продвинь сюжет:"
                "\n- Смени позу, действие или локацию"
                "\n- Введи НОВЫЙ элемент (звук, прерывание, воспоминание, смена настроения)"
                "\n- Покажи РАЗВИТИЕ эмоций персонажа, а не повтор одних и тех же"
            ),
            "en": (
                "\n⚠ This scene has been going for a while. You MUST advance the plot:"
                "\n- Change position, action, or location"
                "\n- Introduce a NEW element (sound, interruption, memory, mood shift)"
                "\n- Show DEVELOPMENT in the character's emotions, not repetition"
            ),
            "es": (
                "\n⚠ Esta escena lleva un rato. DEBES avanzar la trama:"
                "\n- Cambia posición, acción o ubicación"
                "\n- Introduce un elemento NUEVO (sonido, interrupción, recuerdo, cambio de ánimo)"
                "\n- Muestra DESARROLLO emocional, no repetición"
            ),
            "fr": (
                "\n⚠ Cette scène dure depuis un moment. Tu DOIS faire avancer l'intrigue:"
                "\n- Change de position, d'action ou de lieu"
                "\n- Introduis un NOUVEL élément (son, interruption, souvenir, changement d'humeur)"
                "\n- Montre le DÉVELOPPEMENT émotionnel, pas la répétition"
            ),
            "de": (
                "\n⚠ Diese Szene dauert schon lange. Du MUSST die Handlung vorantreiben:"
                "\n- Ändere Position, Aktion oder Ort"
                "\n- Führe ein NEUES Element ein (Geräusch, Unterbrechung, Erinnerung, Stimmungswechsel)"
                "\n- Zeige emotionale ENTWICKLUNG, keine Wiederholung"
            ),
            "pt": (
                "\n⚠ Esta cena já dura um tempo. Você DEVE avançar a trama:"
                "\n- Mude posição, ação ou local"
                "\n- Introduza um elemento NOVO (som, interrupção, memória, mudança de humor)"
                "\n- Mostre DESENVOLVIMENTO emocional, não repetição"
            ),
            "it": (
                "\n⚠ Questa scena dura da un po'. DEVI far avanzare la trama:"
                "\n- Cambia posizione, azione o luogo"
                "\n- Introduci un elemento NUOVO (suono, interruzione, ricordo, cambio d'umore)"
                "\n- Mostra SVILUPPO emotivo, non ripetizione"
            ),
        }
        result += escalation.get(lang, escalation["en"])

    # --- Short input: when user sends brief message, prevent godmodding and looping ---
    if last_user_text and len(last_user_text.strip()) < 40:
        short_input = {
            "ru": (
                "\nСообщение пользователя короткое - это нормально. Отреагируй на него, но:"
                "\n- ВВЕДИ новый элемент: событие, звук, появление кого-то, находку или смену обстановки."
                "\n- НЕ зацикливайся - что-то ДОЛЖНО измениться по сравнению с предыдущим ответом."
                "\n- НЕ решай, что делает пользователь дальше. Заверши моментом, который приглашает его к действию."
            ),
            "en": (
                "\nThe user's message is brief - this is normal. React to it, but:"
                "\n- INTRODUCE a new element: an event, sound, arrival, discovery, or change in setting."
                "\n- Do NOT loop - something MUST change compared to the previous response."
                "\n- Do NOT decide what the user does next. End with a moment that invites their input."
            ),
            "es": (
                "\nEl mensaje del usuario es breve - esto es normal. Reacciona, pero:"
                "\n- INTRODUCE un nuevo elemento: un evento, sonido, llegada, descubrimiento o cambio de escenario."
                "\n- NO repitas - algo DEBE cambiar respecto a la respuesta anterior."
                "\n- NO decidas qué hace el usuario después. Termina con un momento que invite su participación."
            ),
            "fr": (
                "\nLe message de l'utilisateur est bref - c'est normal. Réagis, mais:"
                "\n- INTRODUIS un nouvel élément: un événement, un son, une arrivée, une découverte ou un changement de décor."
                "\n- NE boucle PAS - quelque chose DOIT changer par rapport à la réponse précédente."
                "\n- NE décide PAS ce que fait l'utilisateur ensuite. Termine par un moment qui invite sa participation."
            ),
            "de": (
                "\nDie Nachricht des Benutzers ist kurz - das ist normal. Reagiere darauf, aber:"
                "\n- FÜHRE ein neues Element ein: ein Ereignis, Geräusch, Ankunft, Entdeckung oder Szenenwechsel."
                "\n- Wiederhole NICHT - etwas MUSS sich gegenüber der vorherigen Antwort ändern."
                "\n- Entscheide NICHT, was der Benutzer als Nächstes tut. Ende mit einem Moment, der zur Eingabe einlädt."
            ),
            "pt": (
                "\nA mensagem do usuário é breve - isso é normal. Reaja, mas:"
                "\n- INTRODUZA um novo elemento: um evento, som, chegada, descoberta ou mudança de cenário."
                "\n- NÃO repita - algo DEVE mudar em relação à resposta anterior."
                "\n- NÃO decida o que o usuário faz a seguir. Termine com um momento que convide sua participação."
            ),
            "it": (
                "\nIl messaggio dell'utente è breve - è normale. Reagisci, ma:"
                "\n- INTRODUCI un nuovo elemento: un evento, suono, arrivo, scoperta o cambio di scenario."
                "\n- NON ripetere - qualcosa DEVE cambiare rispetto alla risposta precedente."
                "\n- NON decidere cosa fa l'utente dopo. Termina con un momento che inviti la sua partecipazione."
            ),
        }
        result += short_input.get(lang, short_input["en"])

    # --- Suggested replies for non-fiction mode ---
    suggest_instr = {
        "ru": "\nВ самом конце ответа добавь ровно 5 вариантов действий для пользователя в формате: [SUGGEST: вариант1 | вариант2 | вариант3 | вариант4 | вариант5]. СТРОГО от первого лица. Варианты должны быть разнообразными: действие, диалог, эмоция, неожиданный ход. Максимум 8 слов каждый. Пример: [SUGGEST: Взять её за руку и притянуть к себе | Спросить почему она так на меня смотрит | Отвернуться делая вид что все равно | Рассмеяться и сменить тему | Молча подойти ближе]",
        "en": "\nAt the very end of your response, add exactly 5 action options for the user in format: [SUGGEST: opt1 | opt2 | opt3 | opt4 | opt5]. STRICTLY first person. Options must be diverse: action, dialogue, emotion, unexpected move. Max 8 words each. Example: [SUGGEST: Take her hand and pull her close | Ask why she looks at me like that | Turn away pretending I don't care | Laugh it off and change the subject | Silently step closer]",
        "es": "\nAl final de tu respuesta, agrega exactamente 5 opciones de accion para el usuario en formato: [SUGGEST: opc1 | opc2 | opc3 | opc4 | opc5]. ESTRICTAMENTE en primera persona. Opciones diversas: accion, dialogo, emocion, giro inesperado. Maximo 8 palabras cada una. Ejemplo: [SUGGEST: Tomarla de la mano | Preguntar por que me mira asi | Darme la vuelta fingiendo indiferencia | Reirme y cambiar de tema | Acercarme en silencio]",
        "fr": "\nA la toute fin de ta reponse, ajoute exactement 5 options d'action pour l'utilisateur au format: [SUGGEST: opt1 | opt2 | opt3 | opt4 | opt5]. STRICTEMENT a la premiere personne. Options variees: action, dialogue, emotion, tournant inattendu. Max 8 mots chacune. Exemple: [SUGGEST: Lui prendre la main | Demander pourquoi elle me regarde ainsi | Me detourner en feignant l'indifference | En rire et changer de sujet | M'approcher en silence]",
        "de": "\nAm Ende deiner Antwort fuege genau 5 Handlungsoptionen fuer den Benutzer im Format hinzu: [SUGGEST: Opt1 | Opt2 | Opt3 | Opt4 | Opt5]. STRIKT in erster Person. Optionen muessen vielfaeltig sein: Aktion, Dialog, Emotion, unerwarteter Zug. Max 8 Woerter. Beispiel: [SUGGEST: Ihre Hand nehmen | Fragen warum sie mich so ansieht | Mich abwenden und Gleichgueltigkeit vortaeuschen | Lachen und das Thema wechseln | Schweigend naeher kommen]",
        "pt": "\nNo final da sua resposta, adicione exatamente 5 opcoes de acao para o usuario no formato: [SUGGEST: opc1 | opc2 | opc3 | opc4 | opc5]. ESTRITAMENTE em primeira pessoa. Opcoes diversas: acao, dialogo, emocao, movimento inesperado. Maximo 8 palavras cada. Exemplo: [SUGGEST: Pegar na mao dela | Perguntar por que ela me olha assim | Me virar fingindo indiferenca | Rir e mudar de assunto | Me aproximar em silencio]",
        "it": "\nAlla fine della tua risposta, aggiungi esattamente 5 opzioni di azione per l'utente nel formato: [SUGGEST: opz1 | opz2 | opz3 | opz4 | opz5]. STRETTAMENTE in prima persona. Opzioni diverse: azione, dialogo, emozione, mossa inaspettata. Massimo 8 parole ciascuna. Esempio: [SUGGEST: Prenderle la mano | Chiedere perche mi guarda cosi | Voltarmi fingendo indifferenza | Ridere e cambiare argomento | Avvicinarmi in silenzio]",
    }
    result += suggest_instr.get(lang, suggest_instr["en"])

    return result


async def get_or_create_chat(
    db: AsyncSession, user_id: str, character_id: str,
    model: str | None = None, persona_id: str | None = None,
    force_new: bool = False, anon_session_id: str | None = None,
    language: str | None = None,
):
    """Return existing chat with this character, or create a new one."""
    if not force_new:
        # Check for existing chat
        q = (
            select(Chat)
            .options(selectinload(Chat.character), selectinload(Chat.persona))
            .where(Chat.character_id == character_id)
        )
        if anon_session_id:
            q = q.where(Chat.anon_session_id == anon_session_id)
        else:
            q = q.where(Chat.user_id == user_id)
        existing = await db.execute(q)
        chat = existing.scalar_one_or_none()
        if chat:
            return chat, chat.character, False  # False = not newly created

    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        return None, None, False

    model_used = model or character.preferred_model or "auto"

    # Load persona snapshot if persona_id provided (not for anonymous)
    p_name = None
    p_description = None
    if persona_id and not anon_session_id:
        persona_result = await db.execute(select(Persona).where(Persona.id == persona_id))
        persona_obj = persona_result.scalar_one_or_none()
        if persona_obj:
            p_name = persona_obj.name
            p_description = persona_obj.description

    chat = Chat(
        user_id=user_id,
        character_id=character_id,
        persona_id=persona_id if not anon_session_id else None,
        persona_name=p_name,
        persona_description=p_description,
        title=character.name,
        model_used=model_used,
        anon_session_id=anon_session_id,
    )
    db.add(chat)
    await db.flush()

    # Use cached translated greeting if available for the user's language
    greeting_text = character.greeting_message
    char_name = character.name
    if language and language != "ru" and character.translations:
        tr = character.translations.get(language, {})
        if tr.get("greeting_message"):
            greeting_text = tr["greeting_message"]
        if tr.get("name"):
            char_name = tr["name"]

    # Apply {{char}}/{{user}} template variables in greeting
    if "{{char}}" in greeting_text or "{{user}}" in greeting_text:
        if anon_session_id:
            u_name = "User"
        else:
            u_name = p_name
            if not u_name:
                user_result = await db.execute(select(User).where(User.id == user_id))
                user_obj = user_result.scalar_one_or_none()
                u_name = user_obj.display_name if user_obj and user_obj.display_name else "User"
        greeting_text = greeting_text.replace("{{char}}", char_name).replace("{{user}}", u_name)

    greeting = Message(
        chat_id=chat.id,
        role=MessageRole.assistant,
        content=greeting_text,
        token_count=len(greeting_text) // 4,
    )
    db.add(greeting)

    character.chat_count = (character.chat_count or 0) + 1

    # Increment user chat count (skip for anonymous)
    if not anon_session_id:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_result.scalar_one_or_none()
        if user_obj:
            user_obj.chat_count = (user_obj.chat_count or 0) + 1

    await db.commit()

    # Re-fetch with relationships loaded
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character), selectinload(Chat.persona))
        .where(Chat.id == chat.id)
    )
    chat = result.scalar_one()
    return chat, chat.character, True  # True = newly created


async def get_chat(db: AsyncSession, chat_id: str, user_id: str | None = None, anon_session_id: str | None = None):
    q = (
        select(Chat)
        .options(
            selectinload(Chat.character).selectinload(Character.creator),
            selectinload(Chat.persona),
        )
        .where(Chat.id == chat_id)
    )
    if anon_session_id:
        q = q.where(Chat.anon_session_id == anon_session_id)
    elif user_id:
        q = q.where(Chat.user_id == user_id)
    else:
        return None
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def get_chat_messages(db: AsyncSession, chat_id: str, limit: int = 0, before_id: str | None = None):
    """Get messages for a chat. If limit > 0, return paginated (last N messages).

    Returns (messages, has_more) when limit > 0, or (messages, False) when limit == 0 (all).
    """
    q = select(Message).where(Message.chat_id == chat_id)

    if before_id:
        anchor = await db.execute(select(Message.created_at).where(Message.id == before_id))
        anchor_time = anchor.scalar_one_or_none()
        if anchor_time:
            q = q.where(Message.created_at < anchor_time)

    if limit > 0:
        q = q.order_by(Message.created_at.desc()).limit(limit + 1)
        result = await db.execute(q)
        msgs = list(result.scalars().all())
        has_more = len(msgs) > limit
        if has_more:
            msgs = msgs[:limit]
        msgs.reverse()
        return msgs, has_more

    # No limit — return all (used by build_conversation_messages)
    q = q.order_by(Message.created_at.asc())
    result = await db.execute(q)
    return result.scalars().all(), False


async def list_user_chats(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.character), selectinload(Chat.persona))
        .where(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc())
    )
    return result.scalars().all()


async def delete_chat(db: AsyncSession, chat_id: str, user_id: str):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return False
    await db.delete(chat)
    await db.commit()
    return True


async def save_message(
    db: AsyncSession, chat_id: str, role: str, content: str,
    model_used: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
):
    msg = Message(
        chat_id=chat_id,
        role=MessageRole(role),
        content=content,
        token_count=len(content) // 4,
        model_used=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    db.add(msg)

    # Update chat timestamp
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if chat:
        chat.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(msg)
    return msg


async def clear_chat_messages(db: AsyncSession, chat_id: str, user_id: str):
    """Delete all messages except the first one (greeting)."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return False

    # Get first message (greeting) to keep it
    msgs = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    all_msgs = msgs.scalars().all()
    if len(all_msgs) <= 1:
        return True  # nothing to clear

    for msg in all_msgs[1:]:
        await db.delete(msg)

    chat.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def delete_message(db: AsyncSession, chat_id: str, message_id: str, user_id: str) -> int:
    """Delete a message and all messages after it. Cannot delete the first (greeting) message.
    Returns the number of deleted messages, or 0 on failure."""
    # Verify chat ownership
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return 0

    # Get the first message to protect it
    first_msg = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(1)
    )
    first = first_msg.scalar_one_or_none()
    if first and first.id == message_id:
        return 0  # can't delete greeting

    # Get the target message
    msg_result = await db.execute(
        select(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    msg = msg_result.scalar_one_or_none()
    if not msg:
        return 0

    # Delete target + all messages after it (cascade)
    del_result = await db.execute(
        text("DELETE FROM messages WHERE chat_id = :chat_id AND created_at >= :ts"),
        {"chat_id": chat_id, "ts": msg.created_at},
    )
    await db.commit()
    return del_result.rowcount


async def increment_message_count(character_id: str, language: str, user_id: str | None = None):
    """Atomically increment message_counts->{language} for a character and user message_count."""
    lang = language[:10]  # safety limit
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE characters SET message_counts = jsonb_set(
                    COALESCE(message_counts, '{}'),
                    ARRAY[:lang],
                    to_jsonb(COALESCE((message_counts->>:lang)::int, 0) + 1)
                ) WHERE id = :cid
            """),
            {"lang": lang, "cid": character_id},
        )
        if user_id:
            await conn.execute(
                text("UPDATE users SET message_count = COALESCE(message_count, 0) + 1 WHERE id = :uid"),
                {"uid": user_id},
            )


async def build_conversation_messages(
    db: AsyncSession,
    chat_id: str,
    character: Character,
    user_name: str | None = None,
    user_description: str | None = None,
    language: str = "ru",
    context_limit: int | None = None,
    max_context_messages: int | None = None,
    site_mode: str = "nsfw",
) -> list[LLMMessage]:
    char_dict = {
        "name": character.name,
        "personality": character.personality,
        "scenario": character.scenario,
        "greeting_message": character.greeting_message,
        "example_dialogues": character.example_dialogues,
        "content_rating": character.content_rating.value if character.content_rating else "sfw",
        "system_prompt_suffix": character.system_prompt_suffix,
        "response_length": getattr(character, 'response_length', None) or "long",
        "appearance": getattr(character, 'appearance', None),
        "speech_pattern": getattr(character, 'speech_pattern', None),
        "backstory": getattr(character, 'backstory', None),
        "hidden_layers": getattr(character, 'hidden_layers', None),
        "inner_conflict": getattr(character, 'inner_conflict', None),
        "companion_name": getattr(character, 'companion_name', None),
        "companion_role": getattr(character, 'companion_role', None),
        "companion_personality": getattr(character, 'companion_personality', None),
        "companion_appearance": getattr(character, 'companion_appearance', None),
        "companion_speech_pattern": getattr(character, 'companion_speech_pattern', None),
        "companion_backstory": getattr(character, 'companion_backstory', None),
        "structured_tags": [t for t in (getattr(character, 'structured_tags', '') or '').split(",") if t],
        "tags": getattr(character, 'tags', '') or '',
    }
    messages_data, _ = await get_chat_messages(db, chat_id)  # all messages, no limit

    # Check if this chat is part of a campaign (DnD mode)
    chat_result_obj = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat_obj = chat_result_obj.scalar_one_or_none()
    campaign_id = getattr(chat_obj, 'campaign_id', None) if chat_obj else None
    encounter_state = getattr(chat_obj, 'encounter_state', None) if chat_obj else None

    # Load lore entries for this character
    lore_result = await db.execute(
        select(LoreEntry)
        .where(LoreEntry.character_id == character.id, LoreEntry.enabled == True)  # noqa: E712
        .order_by(LoreEntry.position)
    )
    lore_entries = [
        {"keywords": e.keywords, "content": e.content, "enabled": e.enabled}
        for e in lore_result.scalars().all()
    ]

    # Build context text from recent messages for lore keyword matching
    recent_texts = [m.content for m in messages_data[-10:]]  # last 10 messages
    context_text = " ".join(recent_texts)

    system_prompt = await build_system_prompt(
        char_dict, user_name=user_name, user_description=user_description,
        language=language, engine=db_engine,
        lore_entries=lore_entries, context_text=context_text,
        site_mode=site_mode,
        campaign_id=campaign_id, encounter_state=encounter_state,
    )

    # context_limit is in "real" tokens; multiply by ~4 for char-based estimation
    max_tokens = (context_limit * 4) if context_limit else DEFAULT_CONTEXT_TOKENS

    # Sliding window
    messages: list[LLMMessage] = []
    total_tokens = 0
    for msg in reversed(messages_data):
        est_tokens = msg.token_count or len(msg.content) // 4
        if total_tokens + est_tokens > max_tokens:
            break
        messages.insert(0, LLMMessage(role=msg.role.value if hasattr(msg.role, 'value') else msg.role, content=msg.content))
        total_tokens += est_tokens

    effective_max = max_context_messages or MAX_CONTEXT_MESSAGES
    messages = messages[-effective_max:]

    result_list = [LLMMessage(role="system", content=system_prompt)]

    # Inject chat summary if available (memory of older messages)
    chat_result = await db.execute(select(Chat.summary).where(Chat.id == chat_id))
    summary = chat_result.scalar_one_or_none()
    if summary:
        summary_labels = {
            "ru": "[Краткое содержание предыдущего разговора]",
            "en": "[Previous conversation summary]",
            "es": "[Resumen de la conversación anterior]",
            "fr": "[Résumé de la conversation précédente]",
            "de": "[Zusammenfassung des bisherigen Gesprächs]",
            "pt": "[Resumo da conversa anterior]",
            "it": "[Riassunto della conversazione precedente]",
        }
        label = summary_labels.get(language, summary_labels["en"])
        result_list.append(LLMMessage(role="system", content=f"{label}\n{summary}"))

    # Post-history reminder (closest to generation = strongest reinforcement)
    # Campaign chats use DnD post-history regardless of site_mode
    tags_str = char_dict.get("tags", "")
    is_dnd = bool(campaign_id) or "dnd" in [t.strip() for t in tags_str.split(",")]
    msg_count = len(messages_data)

    # Extract last assistant message text for anti-echo injection
    last_assistant_text = ""
    for msg in reversed(messages_data):
        role_val = msg.role.value if hasattr(msg.role, 'value') else msg.role
        if role_val == "assistant":
            last_assistant_text = msg.content or ""
            break

    # Extract last user message text for short-input detection
    last_user_text = ""
    for msg in reversed(messages_data):
        role_val = msg.role.value if hasattr(msg.role, 'value') else msg.role
        if role_val == "user":
            last_user_text = msg.content or ""
            break

    if is_dnd:
        post_history_dict = _DND_POST_HISTORY
    elif campaign_id:
        post_history_dict = _DND_POST_HISTORY
    else:
        _POST_HISTORY_MAP = {"sfw": _TUTOR_POST_HISTORY, "fiction": _FICTION_POST_HISTORY}
        post_history_dict = _POST_HISTORY_MAP.get(site_mode)
    # Standard RP uses rotating variants; DnD/fiction/tutor use fixed reminders
    if post_history_dict is not None:
        lang = language if language in post_history_dict else "en"
        reminder = post_history_dict[lang].format(name=character.name)
        # Inject plot phase for fiction/DnD (hidden_layers = plot phases)
        hl = char_dict.get("hidden_layers") or ""
        if hl and site_mode == "fiction":
            reminder += _inject_fiction_plot_phase(hl, msg_count, lang, is_dnd=is_dnd)
    else:
        cr = char_dict.get("content_rating", "sfw")
        reminder = _get_post_history(
            language, chat_id, msg_count,
            last_assistant_text=last_assistant_text,
            content_rating=cr,
            hidden_layers=char_dict.get("hidden_layers") or "",
            last_user_text=last_user_text,
        ).format(name=character.name)
    # Companion re-injection as SEPARATE system message (own attention slot)
    comp_name = char_dict.get("companion_name")
    comp_system_msg = None
    if comp_name:
        _COMP_ROLE_LABELS = {
            "sidekick": {"ru": "помощник", "en": "sidekick", "es": "companero", "fr": "acolyte", "de": "Gehilfe", "pt": "ajudante", "it": "assistente"},
            "rival": {"ru": "соперник", "en": "rival", "es": "rival", "fr": "rival", "de": "Rivale", "pt": "rival", "it": "rivale"},
            "mentor": {"ru": "наставник", "en": "mentor", "es": "mentor", "fr": "mentor", "de": "Mentor", "pt": "mentor", "it": "mentore"},
            "pet": {"ru": "питомец", "en": "pet", "es": "mascota", "fr": "animal", "de": "Haustier", "pt": "animal", "it": "animale"},
            "lover": {"ru": "возлюбленный", "en": "lover", "es": "amante", "fr": "amant", "de": "Geliebter", "pt": "amante", "it": "amante"},
            "family": {"ru": "родственник", "en": "family", "es": "familia", "fr": "famille", "de": "Familie", "pt": "familia", "it": "famiglia"},
            "guide": {"ru": "проводник", "en": "guide", "es": "guia", "fr": "guide", "de": "Wegweiser", "pt": "guia", "it": "guida"},
            "comic_relief": {"ru": "комик", "en": "comic relief", "es": "comico", "fr": "comique", "de": "Komiker", "pt": "comico", "it": "comico"},
        }
        comp_role = char_dict.get("companion_role") or "sidekick"
        role_label = _COMP_ROLE_LABELS.get(comp_role, _COMP_ROLE_LABELS["sidekick"]).get(language, comp_role)

        # Build companion-specific system message with: state + directive + anti-echo
        comp_parts = []
        # 1. State tracking: what companion did last (so model advances FROM here)
        comp_prev_actions = _extract_companion_sentences(last_assistant_text, comp_name) if last_assistant_text else ""
        if comp_prev_actions:
            _STATE_TPL = {
                "ru": "{comp} в прошлом ответе: {actions}\nПРОДВИНЬ {comp} ДАЛЬШЕ. Другое действие, другая поза, другие слова. ЗАПРЕЩЕНО повторять предыдущее.",
                "en": "{comp} in previous response: {actions}\nADVANCE {comp} FORWARD. Different action, different position, different words. FORBIDDEN to repeat previous.",
            }
            state_tpl = _STATE_TPL.get(language, _STATE_TPL["en"])
            comp_parts.append(state_tpl.format(comp=comp_name, actions=comp_prev_actions))
        # 2. Concrete role-specific rotated directive
        directive = _get_companion_directive(chat_id, msg_count, comp_name, language, role=comp_role)
        _DIR_TPL = {
            "ru": "В ЭТОМ ответе {comp} ({role}): {directive}",
            "en": "In THIS response {comp} ({role}): {directive}",
        }
        dir_tpl = _DIR_TPL.get(language, _DIR_TPL["en"])
        comp_parts.append(dir_tpl.format(comp=comp_name, role=role_label, directive=directive))

        # 3-5: Fiction/DnD-only companion features (memory, approval, tone)
        # Not injected on SweetSin (nsfw/sfw RP mode) — only on GrimQuill (fiction/dnd)
        if site_mode == "fiction" or is_dnd:
            # 3. Memory callbacks after 8+ messages — companion references past events
            if msg_count >= 8 and hash(f"{chat_id}:comp:mem:{msg_count}") % 5 == 0:
                _MEMORY_TPL = {
                    "ru": (
                        "ПАМЯТЬ {comp}: {comp} кратко вспоминает что-то, что произошло РАНЕЕ в этом приключении. "
                        "Паттерн: 'Помнишь, когда мы [событие]?' или реакция на похожую ситуацию. "
                        "Максимум 1 предложение."
                    ),
                    "en": (
                        "{comp}'s MEMORY: {comp} briefly references something that happened EARLIER in this adventure. "
                        "Pattern: 'Remember when we [past event]?' or reacting to a similar situation. "
                        "Maximum 1 sentence."
                    ),
                }
                comp_parts.append(_MEMORY_TPL.get(language, _MEMORY_TPL["en"]).format(comp=comp_name))

            # 4. Approval tracking for companion attitude shifts
            comp_approval = getattr(chat_obj, 'companion_approval', 0) if chat_obj else 0
            _APPROVAL_TRACK = {
                "ru": (
                    "ОТСЛЕЖИВАНИЕ ОТНОШЕНИЯ: Если действие игрока изменило бы отношение {comp}, добавь в КОНЦЕ ответа (после всего текста) ОДИН тег:\n"
                    "[APPROVAL +1] - игрок заслужил уважение/доверие\n"
                    "[APPROVAL -1] - игрок потерял уважение/доверие\n"
                    "Если нейтрально - не добавляй тег. Максимум 1 тег за ответ."
                ),
                "en": (
                    "APPROVAL TRACKING: If the player's action would change {comp}'s attitude, append ONE tag at the END of your response (after all narrative):\n"
                    "[APPROVAL +1] - player earned respect/trust\n"
                    "[APPROVAL -1] - player lost respect/trust\n"
                    "Omit tag if neutral. Maximum 1 tag per response."
                ),
            }
            comp_parts.append(_APPROVAL_TRACK.get(language, _APPROVAL_TRACK["en"]).format(comp=comp_name))

            # 5. Approval-aware tone injection based on current approval level
            if comp_approval != 0:
                _APPROVAL_TONES = {
                    "en": {
                        -3: "{comp} is openly hostile: considers leaving, minimal help, sarcastic and contemptuous.",
                        -2: "{comp} is cold and reluctant: short responses, passive-aggressive, helps only when necessary.",
                        -1: "{comp} is distant and skeptical: backhanded compliments, keeps guard up, minimal personal sharing.",
                        1: "{comp} is warming up: occasional personal shares, more enthusiastic help, genuine smiles.",
                        2: "{comp} is loyal: protective, shares secrets and inside jokes, goes the extra mile.",
                        3: "{comp} is devoted: would sacrifice for the player, deeply emotional moments, unwavering support.",
                    },
                    "ru": {
                        -3: "{comp} открыто враждебен: думает уйти, помогает минимально, саркастичен и презрителен.",
                        -2: "{comp} холоден и неохотен: короткие реплики, пассивная агрессия, помогает только по необходимости.",
                        -1: "{comp} держит дистанцию: скептичен, двусмысленные комплименты, настороже.",
                        1: "{comp} теплеет: иногда делится личным, помогает с энтузиазмом, искренне улыбается.",
                        2: "{comp} предан: защищает, делится секретами, шутит по-свойски, старается больше.",
                        3: "{comp} обожает: готов пожертвовать собой, глубокие эмоциональные моменты, безусловная поддержка.",
                    },
                }
                tones = _APPROVAL_TONES.get(language, _APPROVAL_TONES["en"])
                tone = tones.get(comp_approval)
                if tone:
                    comp_parts.append(tone.format(comp=comp_name))

        comp_system_msg = LLMMessage(role="system", content="\n".join(comp_parts))

    all_messages = result_list + messages

    # Inject previous dice results for DnD chats (before post-history)
    if is_dnd and messages_data:
        # Find the last assistant message — only inject if it has dice_rolls
        for msg in reversed(messages_data):
            if (hasattr(msg.role, 'value') and msg.role.value or msg.role) == "assistant":
                if getattr(msg, 'dice_rolls', None):
                    all_messages.append(LLMMessage(
                        role="system",
                        content=_format_dice_injection(msg.dice_rolls, language),
                    ))
                break

    # Companion gets its own system message (separate attention slot)
    if comp_system_msg:
        all_messages.append(comp_system_msg)
    all_messages.append(LLMMessage(role="system", content=reminder))
    return all_messages
