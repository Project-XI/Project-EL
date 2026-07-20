"use client";

import { motion, useReducedMotion, type HTMLMotionProps } from "motion/react";
import { forwardRef, useState, type FocusEvent, type MouseEvent, type ReactNode } from "react";

const EASE_OUT = [0.25, 0.1, 0.25, 1];
const SPRING_LAYOUT = { type: "spring", stiffness: 300, damping: 30 };
const SPRING_PRESS = { type: "spring", stiffness: 400, damping: 30 };

export interface ExpandingArrowButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  children: ReactNode;
  accentClassName?: string;
  labelClassName?: string;
}

const ARROW_OPACITY = [1, 0.78, 0.54, 0.32, 0.16] as const;

function DottedChevron({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg viewBox="0 0 20 28" fill="none" aria-hidden="true" className={className} style={style}>
      <circle cx="4" cy="4" r="2" fill="currentColor" />
      <circle cx="10" cy="9" r="2" fill="currentColor" />
      <circle cx="16" cy="14" r="2" fill="currentColor" />
      <circle cx="10" cy="19" r="2" fill="currentColor" />
      <circle cx="4" cy="24" r="2" fill="currentColor" />
    </svg>
  );
}

export const ExpandingArrowButton = forwardRef<HTMLButtonElement, ExpandingArrowButtonProps>(
  function ExpandingArrowButton(
    {
      children,
      className,
      accentClassName,
      labelClassName,
      disabled,
      onMouseEnter,
      onMouseLeave,
      onFocus,
      onBlur,
      style,
      ...rest
    },
    ref,
  ) {
    const reduce = useReducedMotion();
    const [hovered, setHovered] = useState(false);
    const [focused, setFocused] = useState(false);

    // Active state drives the arrow expansion.
    const active = !disabled && (hovered || focused);
    const layoutTransition = reduce ? { duration: 0 } : SPRING_LAYOUT;

    const handleMouseEnter = (event: MouseEvent<HTMLButtonElement>) => {
      setHovered(true);
      onMouseEnter?.(event);
    };

    const handleMouseLeave = (event: MouseEvent<HTMLButtonElement>) => {
      setHovered(false);
      onMouseLeave?.(event);
    };

    const handleFocus = (event: FocusEvent<HTMLButtonElement>) => {
      setFocused(true);
      onFocus?.(event);
    };

    const handleBlur = (event: FocusEvent<HTMLButtonElement>) => {
      setFocused(false);
      onBlur?.(event);
    };

    return (
      <motion.button
        ref={ref}
        type="button"
        disabled={disabled}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        whileTap={reduce || disabled ? undefined : { scale: 0.97 }}
        transition={SPRING_PRESS}
        className={className}
        style={{
          position: "relative",
          display: "inline-flex",
          height: "48px",
          minWidth: "160px",
          alignItems: "center",
          overflow: "hidden",
          borderRadius: "100px",
          backgroundColor: "rgba(255, 255, 255, 0.15)", // Glass morph bg
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(255, 255, 255, 0.25)",
          color: "white",
          cursor: disabled ? "default" : "pointer",
          userSelect: "none",
          opacity: disabled ? 0.5 : 1,
          pointerEvents: disabled ? "none" : "auto",
          transition: "background-color 0.2s ease",
          ...style,
        }}
        {...rest}
      >
        <motion.span
          layout="size"
          aria-hidden="true"
          transition={layoutTransition}
          style={{
            position: "absolute",
            top: "6px",
            bottom: "6px",
            left: "6px",
            width: active ? "calc(100% - 12px)" : "36px",
            borderRadius: "100px",
            overflow: "hidden",
            backgroundColor: "white", // Accent expanding color
            color: "#1a1a1a",
            zIndex: 10,
          }}
        >
          <motion.span
            animate={{ opacity: active ? 0 : 1 }}
            transition={{ duration: reduce ? 0 : 0.1, ease: EASE_OUT }}
            style={{
              position: "absolute",
              inset: 0,
              display: "grid",
              placeItems: "center",
            }}
          >
            <DottedChevron style={{ height: "18px", width: "12px" }} />
          </motion.span>

          <span
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-around",
              padding: "0 12px",
            }}
          >
            {ARROW_OPACITY.map((opacity, index) => (
              <motion.span
                key={opacity}
                animate={{
                  opacity: active ? 1 : 0,
                  transform: active && !reduce ? "translateX(0px)" : "translateX(-6px)",
                }}
                transition={{
                  duration: reduce ? 0 : 0.18,
                  delay: active && !reduce ? 0.04 + index * 0.025 : 0,
                  ease: EASE_OUT,
                }}
                style={{
                  color: `rgba(26, 26, 26, ${opacity})`,
                  display: "inline-grid",
                  placeItems: "center",
                }}
              >
                <DottedChevron style={{ height: "18px", width: "12px" }} />
              </motion.span>
            ))}
          </span>
        </motion.span>

        <motion.span
          animate={{
            opacity: active ? 0 : 1,
            transform: active && !reduce ? "translateX(6px)" : "translateX(0px)",
          }}
          transition={{ duration: reduce ? 0 : 0.12, ease: EASE_OUT }}
          style={{
            position: "relative",
            zIndex: 0,
            marginLeft: "56px",
            marginRight: "20px",
            whiteSpace: "nowrap",
            fontSize: "0.95rem",
            fontWeight: 500,
            letterSpacing: "-0.01em",
          }}
        >
          {children}
        </motion.span>
      </motion.button>
    );
  },
);
