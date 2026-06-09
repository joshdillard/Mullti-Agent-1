import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const WORDS = ["i", "am", "josh", "dillard"];

// Frames between the entrance of each word.
const STAGGER = 8;

const Word: React.FC<{ text: string; index: number }> = ({ text, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delay = index * STAGGER;
  const local = frame - delay;

  // Spring drives a slide-up + scale entrance.
  const entrance = spring({
    frame: local,
    fps,
    config: { damping: 200, mass: 0.6 },
  });

  const translateY = interpolate(entrance, [0, 1], [60, 0]);
  const scale = interpolate(entrance, [0, 1], [0.85, 1]);
  const opacity = interpolate(local, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // The name ("josh dillard") gets emphasis.
  const isName = index >= 2;

  return (
    <span
      style={{
        display: "inline-block",
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
        color: isName ? "#ffffff" : "rgba(255,255,255,0.65)",
        fontWeight: isName ? 800 : 500,
        marginRight: 24,
      }}
    >
      {text}
    </span>
  );
};

export const MyComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Gentle fade-out at the very end.
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #7c3aed 100%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          fontSize: 130,
          lineHeight: 1.1,
          letterSpacing: -2,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        {WORDS.map((word, i) => (
          <Word key={word} text={word} index={i} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
