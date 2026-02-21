interface Choice {
  number: number;
  text: string;
}

interface ChoiceButtonsProps {
  choices: Choice[];
  onChoiceClick: (text: string) => void;
  disabled?: boolean;
}

export default function ChoiceButtons({ choices, onChoiceClick, disabled }: ChoiceButtonsProps) {
  return (
    <div className="flex flex-col gap-2 px-4 py-3">
      {choices.map((choice) => (
        <button
          key={choice.number}
          onClick={() => onChoiceClick(choice.text)}
          disabled={disabled}
          className="w-full text-left px-4 py-3 rounded-lg border border-gray-600 bg-gray-800/50 hover:bg-gray-700/70 hover:border-gray-500 transition-colors text-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span className="text-purple-400 font-semibold mr-2">{choice.number}.</span>
          {choice.text}
        </button>
      ))}
    </div>
  );
}
