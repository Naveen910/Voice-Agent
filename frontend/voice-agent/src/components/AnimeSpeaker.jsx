import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

export default function AnimeSpeaker({ audioStream, expression }) {
  const mountRef = useRef();
  const avatarRef = useRef();
  const mixerRef = useRef();
  const analyserRef = useRef();
  const exprRef = useRef(expression); // keep expression live

  useEffect(() => {
    exprRef.current = expression;
  }, [expression]);

  useEffect(() => {
    if (!mountRef.current) return;

    // Clear any old canvas (fix duplicate issue)
    while (mountRef.current.firstChild) {
      mountRef.current.removeChild(mountRef.current.firstChild);
    }

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      100
    );
    camera.position.set(0, 1.5, 2);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    mountRef.current.appendChild(renderer.domElement);

    // Lighting
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(0, 10, 10);
    scene.add(directionalLight);
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));

    // Load Avatar
    const loader = new GLTFLoader();
    loader.load(
      "/models/Glenda.glb",
      (gltf) => {
        const avatar = gltf.scene;
        avatar.position.set(0, 0, 0);
        scene.add(avatar);
        avatarRef.current = avatar;

        if (gltf.animations.length > 0) {
          const mixer = new THREE.AnimationMixer(avatar);
          mixerRef.current = mixer;
          gltf.animations.forEach((clip) => mixer.clipAction(clip).play());
        }
      },
      undefined,
      (error) => console.error("Failed to load avatar:", error)
    );

    // Audio analyser (if stream provided initially)
    if (audioStream) {
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(audioStream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
    }

    const clock = new THREE.Clock();

    const animate = () => {
      requestAnimationFrame(animate);
      const delta = clock.getDelta();

      if (mixerRef.current) mixerRef.current.update(delta);

      // Lip-sync
      if (avatarRef.current && analyserRef.current) {
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((a, b) => a + b, 0) / dataArray.length / 255;

        if (avatarRef.current.morphTargetInfluences) {
          avatarRef.current.morphTargetInfluences[0] = volume;
        }
      }

      // Expressions
      if (avatarRef.current) {
        if (exprRef.current === "smile") {
          avatarRef.current.rotation.y = Math.sin(Date.now() * 0.002) * 0.05;
        } else if (exprRef.current === "angry") {
          avatarRef.current.rotation.y = Math.sin(Date.now() * 0.01) * 0.1;
        } else {
          avatarRef.current.rotation.y = 0;
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      renderer.dispose();
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, []); // only run once

  // Update analyser if audioStream changes
  useEffect(() => {
    if (audioStream) {
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(audioStream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
    }
  }, [audioStream]);

  return (
    <div
      ref={mountRef}
      style={{ width: "100%", height: "500px", margin: "0 auto", alignItems: "center", display: "flex" }}
    />
  );
}
