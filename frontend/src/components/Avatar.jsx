import { useAnimations, useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { button, useControls } from "leva";
import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { useChat } from "../hooks/useChat";

const facialExpressions = {
  default: {},
  smile: {
    browInnerUp: 0.17,
    eyeSquintLeft: 0.4,
    eyeSquintRight: 0.44,
    noseSneerLeft: 0.17,
    noseSneerRight: 0.14,
    mouthPressLeft: 0.61,
    mouthPressRight: 0.41,
  },
  // ... add other expressions as needed
};

const corresponding = {
  A: "viseme_PP",
  B: "viseme_kk",
  C: "viseme_I",
  D: "viseme_AA",
  E: "viseme_O",
  F: "viseme_U",
  G: "viseme_FF",
  H: "viseme_TH",
  X: "viseme_PP",
};

let setupMode = false;

  useGLTF.preload("/models/Friday.glb");
  useGLTF.preload("/models/animations.glb");

export function Avatar(props) {
  const { nodes, materials } = useGLTF("/models/Friday.glb");
  const { animations } = useGLTF("/models/animations.glb");
  const group = useRef();
  const { actions, mixer } = useAnimations(animations, group);


  const [animation, setAnimation] = useState(
    animations.find((a) => a.name === "Idle")?.name || animations[0]?.name
  );
  const [facialExpression, setFacialExpression] = useState("smile");
  const [lipsync, setLipsync] = useState({ mouthCues: [] });

  const { message, onMessagePlayed, chat, audioToPlay, setAudioToPlay } = useChat();

  const audioRef = useRef();

// Play audio safely on user-triggered event
useEffect(() => {
  if (!audioToPlay) return;

  try {
    const audioBlob = new Blob(
      [Uint8Array.from(atob(audioToPlay), (c) => c.charCodeAt(0))],
      { type: "audio/mp3" }
    );
    const audioUrl = URL.createObjectURL(audioBlob);
    const audioObj = new Audio(audioUrl);

    audioObj.onended = onMessagePlayed;
    audioRef.current = audioObj;

    audioObj.play().catch((err) => console.warn("Audio play failed:", err));
    setAudioToPlay(null); // reset after playing
  } catch (err) {
    console.error("Failed to create audio:", err);
  }
}, [audioToPlay]);


  // Set animation safely
  useEffect(() => {
  if (!actions || !animation || !actions[animation]) return;
  const action = actions[animation];
  action.reset().fadeIn(0.5).play();
  return () => action.fadeOut(0.5);
}, [animation, actions]);


  // Update avatar when a new message arrives
  useEffect(() => {
    if (!message || message.role === "user") {
      setAnimation("Idle");
      setFacialExpression("smile");
      setLipsync({ mouthCues: [] });
      return;
    }

    setAnimation(message.animation || "Idle");
    setFacialExpression(message.facialExpression || "smile");
    setLipsync(message.lipsync || { mouthCues: [] });
  }, [message]);


  // Morph target helper
  const lerpMorphTarget = (target, value, speed = 0.1) => {
    if (!nodes || !group.current) return;
    group.current.traverse((child) => {
      if (child.isSkinnedMesh && child.morphTargetDictionary) {
        const index = child.morphTargetDictionary[target];
        if (index === undefined || child.morphTargetInfluences[index] === undefined) return;
        child.morphTargetInfluences[index] = THREE.MathUtils.lerp(
          child.morphTargetInfluences[index],
          value,
          speed
        );
      }
    });
  };

  // Lip-sync & facial expression update
  useFrame(() => {
    if (!setupMode) {
      // Facial expression morphs
      const mapping = facialExpressions[facialExpression];
      if (mapping) {
        Object.keys(mapping).forEach((key) => lerpMorphTarget(key, mapping[key], 0.1));
      }

      // Lip-sync
      if (message && lipsync && audioRef.current) {
        const currentTime = audioRef.current.currentTime;
        const appliedMorphs = [];
        lipsync.mouthCues.forEach((cue) => {
          if (currentTime >= cue.start && currentTime <= cue.end) {
            const morphName = corresponding[cue.value];
            lerpMorphTarget(morphName, 1, 0.2);
            appliedMorphs.push(morphName);
          }
        });
        Object.values(corresponding).forEach((v) => {
          if (!appliedMorphs.includes(v)) lerpMorphTarget(v, 0, 0.1);
        });
      }
    }
  });

  return (
    <group {...props} dispose={null} ref={group}>
      <primitive object={nodes.Hips} />
      {["Body", "Outfit_Bottom", "Outfit_Footwear", "Outfit_Top", "Hair", "Head", "Teeth"].map((part) => (
        <skinnedMesh
          key={part}
          name={`Wolf3D_${part}`}
          geometry={nodes[`Wolf3D_${part}`].geometry}
          material={materials[`Wolf3D_${part}`] || materials.Wolf3D_Skin}
          skeleton={nodes[`Wolf3D_${part}`].skeleton}
          morphTargetDictionary={nodes[`Wolf3D_${part}`]?.morphTargetDictionary}
          morphTargetInfluences={nodes[`Wolf3D_${part}`]?.morphTargetInfluences}
        />
      ))}
      {["EyeLeft", "EyeRight"].map((eye) => (
        <skinnedMesh
          key={eye}
          name={eye}
          geometry={nodes[eye].geometry}
          material={materials.Wolf3D_Eye}
          skeleton={nodes[eye].skeleton}
          morphTargetDictionary={nodes[eye].morphTargetDictionary}
          morphTargetInfluences={nodes[eye].morphTargetInfluences}
        />
      ))}
    </group>
  );
}