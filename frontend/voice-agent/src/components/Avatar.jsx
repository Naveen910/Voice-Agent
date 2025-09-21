import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMExpressionPresetName } from "@pixiv/three-vrm";

const Avatar = ({ audioStream, expression, handsPose = "wave" }) => {
  const containerRef = useRef(null);
  const vrmRef = useRef(null);
  const rendererRef = useRef(null);
  const waveAnimRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // --- Scene & Camera ---
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 20);
    camera.position.set(0, 1.6, 2.5);  // Waist-up framing
    camera.lookAt(0, 1.2, 0);

    // --- Renderer ---
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(400, 400);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // --- Light ---
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(1, 1, 1).normalize();
    scene.add(light);

    // --- Clock ---
    const clock = new THREE.Clock();

    // --- Load VRM ---
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      "/models/Glenda.vrm",
      (gltf) => {
        const vrm = gltf.userData.vrm;

        // Remove previous VRM if exists
        if (vrmRef.current) {
          scene.remove(vrmRef.current.scene);
          vrmRef.current = null;
        }

        // Add new VRM
        scene.add(vrm.scene);
        vrmRef.current = vrm;

        // Neutral pose & forward
        vrm.scene.rotation.y = Math.PI;
        vrm.scene.position.set(0, 0, 1);

        console.log("✅ VRM loaded (single instance)", vrm);

        // Apply initial hands pose
        applyHandsPose(handsPose);
      },
      (progress) =>
        console.log("Loading VRM...", ((progress.loaded / progress.total) * 100).toFixed(2), "%"),
      (error) => console.error("VRM load error:", error)
    );

    // --- Animation Loop ---
    const animate = () => {
      requestAnimationFrame(animate);
      if (vrmRef.current) vrmRef.current.update(clock.getDelta());
      renderer.render(scene, camera);
    };
    animate();

    // --- Cleanup ---
    return () => {
      if (vrmRef.current) scene.remove(vrmRef.current.scene);
      if (renderer) {
        renderer.dispose();
        renderer.domElement.remove();
      }
      if (waveAnimRef.current) cancelAnimationFrame(waveAnimRef.current);
    };
  }, []);

  // --- Lip Sync ---
  useEffect(() => {
    if (!audioStream) return;

    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(audioStream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const updateLipSync = () => {
      if (!vrmRef.current) return;
      analyser.getByteFrequencyData(dataArray);
      const volume = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;

      if (vrmRef.current.expressionManager) {
        vrmRef.current.expressionManager.setValue(
          VRMExpressionPresetName.A,
          Math.min(volume / 100, 1)
        );
      }
      requestAnimationFrame(updateLipSync);
    };
    updateLipSync();
  }, [audioStream]);

  // --- Expressions ---
  useEffect(() => {
    if (!vrmRef.current || !vrmRef.current.expressionManager) return;

    const em = vrmRef.current.expressionManager;
    em.setValue(VRMExpressionPresetName.Happy, expression === "smile" ? 1 : 0);
    em.setValue(VRMExpressionPresetName.Angry, expression === "angry" ? 1 : 0);
    em.setValue(VRMExpressionPresetName.Neutral, expression === "neutral" ? 1 : 0);
  }, [expression]);

  // --- Hands Pose ---
  const applyHandsPose = (pose) => {
    if (!vrmRef.current || !vrmRef.current.humanoid) return;
    const humanoid = vrmRef.current.humanoid;

    // Cancel previous wave animation
    if (waveAnimRef.current) cancelAnimationFrame(waveAnimRef.current);

    switch (pose) {
      case "down":
        humanoid.setPose({
          rightUpperArm: { x: 0, y: 0, z: 0 },
          leftUpperArm: { x: 0, y: 0, z: 0 },
          rightLowerArm: { x: 0, y: 0, z: 0 },
          leftLowerArm: { x: 0, y: 0, z: 0 },
        });
        break;

      case "up":
        humanoid.setPose({
          rightUpperArm: { x: -1.0, y: 0, z: 0.2 },
          leftUpperArm: { x: -1.0, y: 0, z: -0.2 },
          rightLowerArm: { x: -0.5, y: 0, z: 0 },
          leftLowerArm: { x: -0.5, y: 0, z: 0 },
        });
        break;

      case "wave":
        humanoid.setPose({
          rightUpperArm: { x: -1.0, y: 0, z: 0.2 },
          rightLowerArm: { x: -0.8, y: 0, z: 0 },
          leftUpperArm: { x: 0, y: 0, z: 0 },
          leftLowerArm: { x: 0, y: 0, z: 0 },
        });

        let t = 0;
        const waveAnim = () => {
          if (!vrmRef.current) return;
          const hand = humanoid.getBoneNode("rightHand");
          if (hand) hand.rotation.z = Math.sin(t) * 0.5;
          t += 0.1;
          waveAnimRef.current = requestAnimationFrame(waveAnim);
        };
        waveAnim();
        break;

      default:
        console.warn("Unknown hands pose:", pose);
    }
  };

  // Apply hands pose whenever prop changes
  useEffect(() => {
    applyHandsPose(handsPose);
  }, [handsPose]);

  return <div ref={containerRef} />;
};

export default Avatar;
