from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import Persona
from app.personas.schemas import PersonaCreate, PersonaUpdate
from app.utils.sanitize import strip_html_tags

router = APIRouter(prefix="/api/personas", tags=["personas"])

MAX_PERSONAS = 10


def _serialize(p: Persona) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "is_default": p.is_default,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("")
async def list_personas(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Persona)
        .where(Persona.user_id == user["id"])
        .order_by(Persona.created_at)
    )
    return [_serialize(p) for p in result.scalars().all()]


@router.post("", status_code=201)
async def create_persona(
    body: PersonaCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check limit
    count = await db.execute(
        select(func.count()).select_from(Persona).where(Persona.user_id == user["id"])
    )
    if (count.scalar() or 0) >= MAX_PERSONAS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_PERSONAS} personas allowed")

    # If setting as default, clear others
    if body.is_default:
        await db.execute(
            update(Persona)
            .where(Persona.user_id == user["id"], Persona.is_default == True)  # noqa: E712
            .values(is_default=False)
        )

    persona = Persona(
        user_id=user["id"],
        name=strip_html_tags(body.name),
        description=strip_html_tags(body.description) if body.description else None,
        is_default=body.is_default,
    )
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return _serialize(persona)


@router.put("/{persona_id}")
async def update_persona(
    persona_id: str,
    body: PersonaUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.user_id == user["id"])
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    if body.name is not None:
        persona.name = strip_html_tags(body.name)
    if body.description is not None:
        persona.description = strip_html_tags(body.description) if body.description else None
    if body.is_default is not None:
        if body.is_default:
            await db.execute(
                update(Persona)
                .where(Persona.user_id == user["id"], Persona.is_default == True)  # noqa: E712
                .values(is_default=False)
            )
        persona.is_default = body.is_default

    await db.commit()
    await db.refresh(persona)
    return _serialize(persona)


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.user_id == user["id"])
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Chat.persona_id will be SET NULL by DB FK constraint
    await db.delete(persona)
    await db.commit()
