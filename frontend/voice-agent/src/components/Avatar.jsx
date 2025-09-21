import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMExpressionPresetName } from "@pixiv/three-vrm";

const Avatar = ({ audioStream, expression }) => {
  const containerRef = useRef(null);
  const vrmRef = useRef(null);

  useEffect(() => {
    let renderer, scene, camera, clock;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(30, 1, 0.1, 20);
    camera.position.set(0, 1.4, 2.5);

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(400, 400);
    containerRef.current.appendChild(renderer.domElement);

    clock = new THREE.Clock();

    const light = new THREE.DirectionalLight(0xffffff);
    light.position.set(1, 1, 1).normalize();
    scene.add(light);

    const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));

loader.load(
  "/models/Glenda.vrm",
  (gltf) => {
    const vrm = gltf.userData.vrm; 
    scene.add(vrm.scene);
    vrmRef.current = vrm;
    vrm.scene.rotation.y = Math.PI; // 180 degrees
    camera.position.set(0, 1.4, 2.5);
    camera.lookAt(0, 1.4, 0); 
    console.log("✅ VRM model loaded:", vrm);
  },
  (progress) => console.log("Loading model...", (progress.loaded / progress.total) * 100, "%"),
  (error) => console.error(error)
);


    const animate = () => {
      requestAnimationFrame(animate);
      if (vrmRef.current) vrmRef.current.update(clock.getDelta());
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      if (renderer) renderer.dispose();
    };
  }, []);

  // Lip Sync
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

      if (vrmRef.current?.expressionManager) {
          vrmRef.current.expressionManager.setValue(
          VRMExpressionPresetName.A,
          Math.min(volume / 100, 1.0)
          );
        }

      requestAnimationFrame(updateLipSync);
    };
    updateLipSync();
  }, [audioStream]);

  // Expression Handling
  useEffect(() => {
    if (!vrmRef.current) return;

    if (vrmRef.current?.expressionManager) {
  vrmRef.current.expressionManager.setValue(
    VRMExpressionPresetName.Happy,
    expression === "smile" ? 1.0 : 0.0
  );
  vrmRef.current.expressionManager.setValue(
    VRMExpressionPresetName.Angry,
    expression === "angry" ? 1.0 : 0.0
  );
  vrmRef.current.expressionManager.setValue(
    VRMExpressionPresetName.Neutral,
    expression === "neutral" ? 1.0 : 0.0
  );
}

  }, [expression]);

  return <div ref={containerRef} />;
};

export default Avatar;
