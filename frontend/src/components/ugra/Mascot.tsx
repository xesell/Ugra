import { useEffect, useRef, useState } from "react";
import { ugraAsset } from "@/assets/ugra";
import { cn } from "@/lib/utils";
import {
  type AgentState,
  IDLE_CYCLE_MS,
  IDLE_CYCLE_POSES,
  IDLE_DELAY_MS,
  MASCOT_FADE_MS,
  MASCOT_STATES,
} from "./mascotConfig";

interface MascotProps {
  state: AgentState;
  height?: number;
  className?: string;
  /** When true, allow idle pose cycling after IDLE_DELAY_MS */
  enableIdle?: boolean;
}

export function Mascot({ state, height = 320, className, enableIdle = true }: MascotProps) {
  const config = MASCOT_STATES[state];
  const activePose = config.pose;

  const [displaySrc, setDisplaySrc] = useState(() => ugraAsset(activePose));
  const [opacity, setOpacity] = useState(1);
  const [idlePose, setIdlePose] = useState<string | null>(null);
  const lastStateChange = useRef(Date.now());
  const prevPose = useRef(activePose);
  const fadeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const targetPose = idlePose ?? activePose;
  const targetSrc = ugraAsset(targetPose);

  // Track state changes — reset idle
  useEffect(() => {
    lastStateChange.current = Date.now();
    setIdlePose(null);
  }, [state]);

  // Idle animation after 20s without state change
  useEffect(() => {
    if (!enableIdle) return;

    const checkIdle = setInterval(() => {
      const elapsed = Date.now() - lastStateChange.current;
      if (elapsed >= IDLE_DELAY_MS) {
        setIdlePose((prev) => {
          if (prev) return prev;
          return IDLE_CYCLE_POSES[0];
        });
      }
    }, 1000);

    return () => clearInterval(checkIdle);
  }, [enableIdle, state]);

  // Cycle idle poses every IDLE_CYCLE_MS
  useEffect(() => {
    if (!idlePose) return;

    const cycle = setInterval(() => {
      setIdlePose((cur) => {
        if (!cur) return IDLE_CYCLE_POSES[0];
        const idx = IDLE_CYCLE_POSES.indexOf(cur as (typeof IDLE_CYCLE_POSES)[number]);
        return IDLE_CYCLE_POSES[(idx + 1) % IDLE_CYCLE_POSES.length];
      });
    }, IDLE_CYCLE_MS);

    return () => clearInterval(cycle);
  }, [idlePose === null]);

  // Crossfade between poses
  useEffect(() => {
    if (targetSrc === displaySrc && targetPose === prevPose.current) return;

    clearTimeout(fadeTimer.current);
    setOpacity(0);

    fadeTimer.current = setTimeout(() => {
      const img = new Image();
      img.onload = () => {
        setDisplaySrc(targetSrc);
        prevPose.current = targetPose;
        requestAnimationFrame(() => setOpacity(1));
      };
      img.onerror = () => {
        setDisplaySrc(targetSrc);
        setOpacity(1);
      };
      img.src = targetSrc;
    }, MASCOT_FADE_MS);

    return () => clearTimeout(fadeTimer.current);
  }, [targetSrc, targetPose, displaySrc]);

  return (
    <div
      className={cn("relative flex items-end justify-center", className)}
      style={{ height, minWidth: height * 0.85 }}
    >
      <img
        src={displaySrc}
        alt="Ugra"
        className="max-h-full w-auto object-contain drop-shadow-lg"
        style={{
          opacity,
          transition: `opacity ${MASCOT_FADE_MS}ms ease-in-out`,
          maxHeight: height,
        }}
        draggable={false}
      />
    </div>
  );
}
