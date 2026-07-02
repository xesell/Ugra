import { ugraAsset, ugraPoseForEvent } from "@/assets/ugra";
import { cn } from "@/lib/utils";

interface UgraCharacterProps {
  /** Asset key like "states/greeting" or event type like "VacancyFound" */
  pose?: string;
  size?: number;
  className?: string;
  alt?: string;
}

export function UgraCharacter({
  pose = "states/greeting",
  size = 120,
  className,
  alt = "Ugra",
}: UgraCharacterProps) {
  const src = pose.includes("/") ? ugraAsset(pose) : ugraPoseForEvent(pose);

  return (
    <img
      src={src}
      alt={alt}
      width={size}
      height={size}
      className={cn("object-contain drop-shadow-sm", className)}
      draggable={false}
    />
  );
}
