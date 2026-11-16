"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Sparkles, Shield, Cpu, Activity, RotateCw, CheckCircle2 } from "lucide-react";

export default function ThreeHeroShape() {
  const containerRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [pulseActive, setPulseActive] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Dimensions
    const width = container.clientWidth || 450;
    const height = container.clientHeight || 420;

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 7.2);

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    container.appendChild(renderer.domElement);

    // Master 3D Group
    const masterGroup = new THREE.Group();
    scene.add(masterGroup);

    // Sub-group for tilt & rotation
    const modelGroup = new THREE.Group();
    masterGroup.add(modelGroup);

    // -------------------------------------------------------------
    // 1. Central Faceted Truth Prism (Icosahedron)
    // -------------------------------------------------------------
    const coreGeo = new THREE.IcosahedronGeometry(1.3, 0);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x141812,
      roughness: 0.12,
      metalness: 0.88,
      flatShading: true,
      emissive: 0x1a3300,
      emissiveIntensity: 0.35,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    modelGroup.add(coreMesh);

    // Sharp Razor Edges (TruthScan Acid Lime Wireframe)
    const edgesGeo = new THREE.EdgesGeometry(coreGeo);
    const edgesMat = new THREE.LineBasicMaterial({
      color: 0xb7ff3c,
      linewidth: 2,
    });
    const edgesMesh = new THREE.LineSegments(edgesGeo, edgesMat);
    edgesMesh.scale.setScalar(1.002);
    modelGroup.add(edgesMesh);

    // Inner Luminous Core (Glowing Mini Octahedron)
    const innerGeo = new THREE.OctahedronGeometry(0.65, 0);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0xb7ff3c,
      wireframe: true,
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    modelGroup.add(innerMesh);

    // -------------------------------------------------------------
    // 2. Orbital Gimbal Rings (TruthScan Hardware Aesthetic)
    // -------------------------------------------------------------
    // Ring A: Horizontal Scanner Ring (Acid Lime #B7FF3C)
    const ringAGeo = new THREE.TorusGeometry(2.2, 0.04, 16, 100);
    const ringAMat = new THREE.MeshStandardMaterial({
      color: 0xb7ff3c,
      roughness: 0.15,
      metalness: 0.9,
      emissive: 0x3d7000,
      emissiveIntensity: 0.5,
    });
    const ringAMesh = new THREE.Mesh(ringAGeo, ringAMat);
    ringAMesh.rotation.x = Math.PI / 2;
    modelGroup.add(ringAMesh);

    // Ring B: Vertical Gimbal Ring (Clean Paper White #F5F1E8)
    const ringBGeo = new THREE.TorusGeometry(2.45, 0.03, 16, 100);
    const ringBMat = new THREE.MeshStandardMaterial({
      color: 0xf5f1e8,
      roughness: 0.25,
      metalness: 0.75,
      transparent: true,
      opacity: 0.85,
    });
    const ringBMesh = new THREE.Mesh(ringBGeo, ringBMat);
    modelGroup.add(ringBMesh);

    // Ring C: Diagonal Tactical Ring (Graphite Ink with Verdict Accents)
    const ringCGeo = new THREE.TorusGeometry(2.7, 0.02, 16, 100);
    const ringCMat = new THREE.MeshBasicMaterial({
      color: 0x888888,
      transparent: true,
      opacity: 0.45,
    });
    const ringCMesh = new THREE.Mesh(ringCGeo, ringCMat);
    ringCMesh.rotation.x = Math.PI / 4;
    ringCMesh.rotation.y = Math.PI / 4;
    modelGroup.add(ringCMesh);

    // -------------------------------------------------------------
    // 3. Four Cardinal Status Nodes (Verified, Ingesting, Analyzing, Corroborating)
    // -------------------------------------------------------------
    const nodeGroup = new THREE.Group();
    modelGroup.add(nodeGroup);

    const nodeColors = [0xb7ff3c, 0xff4d4d, 0xb7ff3c, 0xffc857]; // Lime, Red, Lime, Amber
    const cardinalNodes = [];

    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI) / 2;
      const nodeGeo = new THREE.BoxGeometry(0.2, 0.2, 0.2);
      const nodeMat = new THREE.MeshStandardMaterial({
        color: nodeColors[i],
        roughness: 0.2,
        metalness: 0.8,
        flatShading: true,
      });
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);

      // Node black border
      const nodeEdgesGeo = new THREE.EdgesGeometry(nodeGeo);
      const nodeEdgesMat = new THREE.LineBasicMaterial({ color: 0x111111, linewidth: 2 });
      const nodeEdgesMesh = new THREE.LineSegments(nodeEdgesGeo, nodeEdgesMat);
      nodeMesh.add(nodeEdgesMesh);

      nodeMesh.position.set(Math.cos(angle) * 2.2, 0, Math.sin(angle) * 2.2);
      nodeGroup.add(nodeMesh);
      cardinalNodes.push(nodeMesh);
    }

    // -------------------------------------------------------------
    // 4. Orbiting Data Voxels & Particles (Consensus Mesh)
    // -------------------------------------------------------------
    const voxelGroup = new THREE.Group();
    modelGroup.add(voxelGroup);

    const voxelCount = 18;
    const voxels = [];
    for (let i = 0; i < voxelCount; i++) {
      const vGeo = new THREE.BoxGeometry(0.12, 0.12, 0.12);
      const isLime = i % 3 === 0;
      const vMat = new THREE.MeshBasicMaterial({
        color: isLime ? 0xb7ff3c : 0xf5f1e8,
        wireframe: i % 2 === 0,
      });
      const vMesh = new THREE.Mesh(vGeo, vMat);

      const radius = 2.0 + Math.random() * 1.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      vMesh.position.set(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi)
      );

      voxelGroup.add(vMesh);
      voxels.push({
        mesh: vMesh,
        speedX: (Math.random() - 0.5) * 0.02,
        speedY: (Math.random() - 0.5) * 0.02,
        rotSpeed: (Math.random() - 0.5) * 0.05,
      });
    }

    // Background Star/Particle Points
    const ptCount = 200;
    const ptPositions = new Float32Array(ptCount * 3);
    for (let i = 0; i < ptCount; i++) {
      const r = 2.4 + Math.random() * 1.5;
      const th = Math.random() * Math.PI * 2;
      const ph = Math.acos(Math.random() * 2 - 1);

      ptPositions[i * 3] = r * Math.sin(ph) * Math.cos(th);
      ptPositions[i * 3 + 1] = r * Math.sin(ph) * Math.sin(th);
      ptPositions[i * 3 + 2] = r * Math.cos(ph);
    }
    const ptGeo = new THREE.BufferGeometry();
    ptGeo.setAttribute("position", new THREE.BufferAttribute(ptPositions, 3));
    const ptMat = new THREE.PointsMaterial({
      color: 0xb7ff3c,
      size: 0.045,
      transparent: true,
      opacity: 0.75,
    });
    const ptMesh = new THREE.Points(ptGeo, ptMat);
    modelGroup.add(ptMesh);

    // -------------------------------------------------------------
    // 5. Lighting
    // -------------------------------------------------------------
    const ambLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambLight);

    const limeKeyLight = new THREE.DirectionalLight(0xb7ff3c, 3.2);
    limeKeyLight.position.set(4, 5, 4);
    scene.add(limeKeyLight);

    const fillLight = new THREE.DirectionalLight(0xf5f1e8, 1.8);
    fillLight.position.set(-4, -3, -4);
    scene.add(fillLight);

    const centerPointLight = new THREE.PointLight(0xb7ff3c, 3.5, 6);
    centerPointLight.position.set(0, 0, 0);
    scene.add(centerPointLight);

    // -------------------------------------------------------------
    // 6. Interactive Drag & Mouse Orbiting
    // -------------------------------------------------------------
    let pointerDown = false;
    let prevMousePos = { x: 0, y: 0 };
    let dragVelocity = { x: 0, y: 0 };
    let autoRotationSpeed = 0.008;
    let targetRotationX = 0;
    let targetRotationY = 0;

    const onPointerDown = (e) => {
      pointerDown = true;
      setIsDragging(true);
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onPointerMove = (e) => {
      if (pointerDown) {
        const deltaX = e.clientX - prevMousePos.x;
        const deltaY = e.clientY - prevMousePos.y;
        dragVelocity.x = deltaX * 0.006;
        dragVelocity.y = deltaY * 0.006;
        modelGroup.rotation.y += dragVelocity.x;
        modelGroup.rotation.x += dragVelocity.y;
        prevMousePos = { x: e.clientX, y: e.clientY };
      } else {
        const rect = container.getBoundingClientRect();
        const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
        targetRotationY = normX * 0.45;
        targetRotationX = normY * 0.35;
      }
    };

    const onPointerUp = () => {
      pointerDown = false;
      setIsDragging(false);
    };

    container.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);

    // Click pulse trigger
    let pulseScale = 1.0;
    const triggerPulse = () => {
      pulseScale = 1.18;
      setPulseActive(true);
      setTimeout(() => setPulseActive(false), 800);
    };
    container.addEventListener("click", triggerPulse);

    // -------------------------------------------------------------
    // 7. Animation Loop
    // -------------------------------------------------------------
    let animationFrameId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Inertia & drag dampening
      if (!pointerDown) {
        dragVelocity.x *= 0.94;
        dragVelocity.y *= 0.94;
        modelGroup.rotation.y += dragVelocity.x;
        modelGroup.rotation.x += dragVelocity.y;

        // Base idle rotation
        modelGroup.rotation.y += autoRotationSpeed;

        // Smooth mouse tilt lerp
        masterGroup.rotation.x += (targetRotationX - masterGroup.rotation.x) * 0.06;
        masterGroup.rotation.y += (targetRotationY - masterGroup.rotation.y) * 0.06;
      }

      // Smooth pulse return
      pulseScale += (1.0 - pulseScale) * 0.1;

      // Inner Core Rotations
      coreMesh.rotation.x += 0.007;
      coreMesh.rotation.z += 0.005;
      edgesMesh.rotation.copy(coreMesh.rotation);

      innerMesh.rotation.x -= 0.015;
      innerMesh.rotation.y += 0.02;

      // Scale pulse breathing
      const breath = (1.0 + Math.sin(elapsed * 2.5) * 0.02) * pulseScale;
      coreMesh.scale.set(breath, breath, breath);
      edgesMesh.scale.set(breath * 1.002, breath * 1.002, breath * 1.002);

      // Orbital Gimbal Rings rotations
      ringAMesh.rotation.z += 0.016; // Lime horizontal ring
      ringBMesh.rotation.y += 0.01;  // White vertical ring
      ringCMesh.rotation.z -= 0.008; // Diagonal ring

      // Cardinal Nodes orbit rotation
      nodeGroup.rotation.y += 0.016;
      cardinalNodes.forEach((node, idx) => {
        node.rotation.x += 0.03;
        node.rotation.y += 0.02;
      });

      // Data voxels movement
      voxels.forEach((v) => {
        v.mesh.rotation.x += v.rotSpeed;
        v.mesh.rotation.y += v.rotSpeed;
      });
      voxelGroup.rotation.y -= 0.004;

      renderer.render(scene, camera);
    };

    animate();

    // Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: nw, height: nh } = entry.contentRect;
        if (nw > 0 && nh > 0) {
          camera.aspect = nw / nh;
          camera.updateProjectionMatrix();
          renderer.setSize(nw, nh);
        }
      }
    });
    resizeObserver.observe(container);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      container.removeEventListener("click", triggerPulse);
      resizeObserver.disconnect();

      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

      [coreGeo, edgesGeo, innerGeo, ringAGeo, ringBGeo, ringCGeo, ptGeo].forEach((g) => g.dispose());
      [coreMat, edgesMat, innerMat, ringAMat, ringBMat, ringCMat, ptMat].forEach((m) => m.dispose());
      renderer.dispose();
    };
  }, []);

  return (
    <div className="relative w-full border-3 border-[#111111] bg-[#111111] shadow-hard-lg overflow-hidden select-none">
      {/* Neo-Brutalist Dot Grid Background */}
      <div
        className="absolute inset-0 pointer-events-none opacity-25"
        style={{
          backgroundImage:
            "radial-gradient(#B7FF3C 1.5px, transparent 1.5px), linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)",
          backgroundSize: "24px 24px, 48px 48px, 48px 48px",
        }}
      />

      {/* Crosshair Corner Markers */}
      <div className="absolute top-12 left-3 font-mono-tech text-xs text-[#B7FF3C]/40 pointer-events-none select-none">+</div>
      <div className="absolute top-12 right-3 font-mono-tech text-xs text-[#B7FF3C]/40 pointer-events-none select-none">+</div>
      <div className="absolute bottom-3 left-3 font-mono-tech text-xs text-[#B7FF3C]/40 pointer-events-none select-none">+</div>

      {/* TruthScan Window Titlebar (Neo-Brutalist Header) */}
      <div className="relative z-10 flex items-center justify-between px-4 py-2.5 bg-[#111111] text-[#F5F1E8] border-b-2 border-white/20">
        <div className="flex items-center gap-2">
          {/* Trademark Traffic Light Dots */}
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 bg-[#FF4D4D] border border-white/60" />
            <div className="w-2.5 h-2.5 bg-[#FFC857] border border-white/60" />
            <div className="w-2.5 h-2.5 bg-[#B7FF3C] border border-white/60" />
          </div>
          <span className="font-mono-tech text-xs text-[#B7FF3C] font-bold tracking-wider ml-1">
            VERIFY_ENGINE.SYS
          </span>
        </div>

        <div className="flex items-center gap-2 font-mono-tech text-[10px] text-[#E8E2D5]/80 uppercase">
          <Activity className="w-3 h-3 text-[#B7FF3C]" />
          <span>3D ORBIT MESH // 60 FPS</span>
        </div>
      </div>

      {/* 3D WebGL Canvas Container */}
      <div
        ref={containerRef}
        className={`relative w-full h-[360px] sm:h-[420px] flex items-center justify-center ${
          isDragging ? "cursor-grabbing" : "cursor-grab"
        }`}
        title="Click or drag to interact with the 3D Truth Core"
      />

      {/* Top HUD Telemetry Overlay */}
      <div className="absolute top-12 left-4 z-10 pointer-events-none space-y-1">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#111111]/90 border border-[#B7FF3C]/50 text-[#B7FF3C] font-mono-tech text-[10px] font-bold uppercase shadow-hard-xs">
          <Cpu className="w-3 h-3" />
          <span>NEURAL CONSENSUS CORE</span>
        </div>
        <div className="font-mono-tech text-[9px] text-[#E8E2D5]/70 pl-0.5 tracking-wider">
          CROSS-REFERENCING: 45,000+ FACT REPOSITORIES
        </div>
      </div>

      {/* Bottom HUD: Live Status & Interaction Prompt */}
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none flex flex-col gap-1">
        <div className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-[#111111]/90 border border-white/20 font-mono-tech text-[9px] text-white/80">
          <span className="w-1.5 h-1.5 rounded-full bg-[#B7FF3C] animate-ping" />
          <span className="text-[#B7FF3C] font-bold">LIVE RADAR ACTIVE</span>
          <span className="text-white/40">•</span>
          <span>DRAG 360° TO ROTATE</span>
        </div>
        {pulseActive && (
          <div className="font-mono-tech text-[9px] text-[#B7FF3C] font-bold animate-pulse">
            &gt;&gt; PULSE WAVE DISPATCHED: CONSENSUS SYNCHRONIZED
          </div>
        )}
      </div>

      {/* Iconic TruthScan Sticker Stamp (Bottom-Right) */}
      <div className="absolute -bottom-1 -right-1 z-10 bg-[#B7FF3C] text-[#111111] border-2 border-[#111111] shadow-hard font-display text-xs uppercase px-3 py-1 font-bold tracking-wider flex items-center gap-1.5 transform hover:scale-105 transition-transform cursor-pointer">
        <Sparkles className="w-3.5 h-3.5 text-[#111111]" />
        <span>AUDITED BY TRUTHSCAN</span>
      </div>
    </div>
  );
}
