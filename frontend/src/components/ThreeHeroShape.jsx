"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Sparkles, Shield, Cpu, Activity, RefreshCw } from "lucide-react";

export default function ThreeHeroShape() {
  const containerRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const [pulseCount, setPulseCount] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Scene & Camera
    const scene = new THREE.Scene();
    const width = container.clientWidth || 400;
    const height = container.clientHeight || 450;

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
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Main 3D Group
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    // 1. Inner Solid Core (Dark Faceted Crystal)
    const coreGeo = new THREE.IcosahedronGeometry(1.25, 0);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x111111,
      roughness: 0.15,
      metalness: 0.9,
      emissive: 0x1f3d05,
      emissiveIntensity: 0.4,
      flatShading: true,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    mainGroup.add(coreMesh);

    // 2. Core Glowing Wireframe Cage
    const coreWireMat = new THREE.MeshBasicMaterial({
      color: 0xb7ff3c,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
    });
    const coreWireMesh = new THREE.Mesh(coreGeo, coreWireMat);
    coreWireMesh.scale.setScalar(1.005);
    mainGroup.add(coreWireMesh);

    // 3. Middle Geodesic Wireframe Shell
    const midGeo = new THREE.IcosahedronGeometry(1.7, 1);
    const midMat = new THREE.MeshBasicMaterial({
      color: 0x22c55e,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
    });
    const midMesh = new THREE.Mesh(midGeo, midMat);
    mainGroup.add(midMesh);

    // 4. Outer Dodecahedron Wireframe Cage
    const outerGeo = new THREE.DodecahedronGeometry(2.1, 0);
    const outerMat = new THREE.MeshBasicMaterial({
      color: 0xe8e2d5,
      wireframe: true,
      transparent: true,
      opacity: 0.2,
    });
    const outerMesh = new THREE.Mesh(outerGeo, outerMat);
    mainGroup.add(outerMesh);

    // 5. Gyroscopic Orbital Ring 1 (Neon Lime Ring)
    const ring1Geo = new THREE.TorusGeometry(2.45, 0.035, 16, 120);
    const ring1Mat = new THREE.MeshStandardMaterial({
      color: 0xb7ff3c,
      roughness: 0.1,
      metalness: 0.95,
      emissive: 0x5fa800,
      emissiveIntensity: 0.7,
    });
    const ring1Mesh = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1Mesh.rotation.x = Math.PI / 3;
    mainGroup.add(ring1Mesh);

    // 6. Gyroscopic Orbital Ring 2 (Metallic Silver Ring)
    const ring2Geo = new THREE.TorusGeometry(2.7, 0.025, 16, 120);
    const ring2Mat = new THREE.MeshStandardMaterial({
      color: 0xe8e2d5,
      roughness: 0.2,
      metalness: 0.8,
      transparent: true,
      opacity: 0.75,
    });
    const ring2Mesh = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2Mesh.rotation.y = Math.PI / 4;
    mainGroup.add(ring2Mesh);

    // 7. Outer Tech Ring (Dashed Horizon Ring)
    const ring3Geo = new THREE.TorusGeometry(2.95, 0.015, 16, 120);
    const ring3Mat = new THREE.MeshBasicMaterial({
      color: 0x888888,
      transparent: true,
      opacity: 0.35,
    });
    const ring3Mesh = new THREE.Mesh(ring3Geo, ring3Mat);
    ring3Mesh.rotation.x = -Math.PI / 6;
    mainGroup.add(ring3Mesh);

    // 8. Floating Neural Point Cloud / Verification Particles
    const particleCount = 380;
    const particlePositions = new Float32Array(particleCount * 3);
    const particleSizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      // Distribute on a spherical shell between r=1.9 and r=3.3
      const radius = 1.9 + Math.random() * 1.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      particlePositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePositions[i * 3 + 2] = radius * Math.cos(phi);

      particleSizes[i] = Math.random() * 0.06 + 0.02;
    }

    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute(
      "position",
      new THREE.BufferAttribute(particlePositions, 3)
    );

    const particleMat = new THREE.PointsMaterial({
      color: 0xb7ff3c,
      size: 0.06,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    mainGroup.add(particleSystem);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xb7ff3c, 2.5);
    dirLight1.position.set(5, 5, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 1.8);
    dirLight2.position.set(-5, -4, -3);
    scene.add(dirLight2);

    const pointLight = new THREE.PointLight(0xb7ff3c, 3, 8);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);

    // Mouse Interaction
    let targetRotationX = 0;
    let targetRotationY = 0;
    let currentRotationX = 0;
    let currentRotationY = 0;

    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      targetRotationY = x * 0.8;
      targetRotationX = y * 0.6;
    };

    const handleMouseLeave = () => {
      targetRotationX = 0;
      targetRotationY = 0;
    };

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);

    // Animation Loop
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse lerp
      currentRotationX += (targetRotationX - currentRotationX) * 0.05;
      currentRotationY += (targetRotationY - currentRotationY) * 0.05;

      // Base rotations
      mainGroup.rotation.x = currentRotationX * 0.8;
      mainGroup.rotation.y = currentRotationY * 0.8;

      // Inner Core rotation
      coreMesh.rotation.x += 0.006;
      coreMesh.rotation.y += 0.009;
      coreWireMesh.rotation.x = coreMesh.rotation.x;
      coreWireMesh.rotation.y = coreMesh.rotation.y;

      // Middle Cage rotation
      midMesh.rotation.x -= 0.004;
      midMesh.rotation.z += 0.005;

      // Outer Cage rotation
      outerMesh.rotation.y += 0.003;
      outerMesh.rotation.z -= 0.002;

      // Orbital Rings rotation
      ring1Mesh.rotation.z += 0.012;
      ring1Mesh.rotation.x += 0.004;

      ring2Mesh.rotation.x -= 0.01;
      ring2Mesh.rotation.y += 0.007;

      ring3Mesh.rotation.y -= 0.006;

      // Particle system gentle oscillation
      particleSystem.rotation.y += 0.002;
      particleSystem.rotation.x = Math.sin(elapsedTime * 0.5) * 0.1;

      // Breathing scale
      const scale = 1 + Math.sin(elapsedTime * 2) * 0.02;
      coreMesh.scale.set(scale, scale, scale);
      coreWireMesh.scale.set(scale * 1.005, scale * 1.005, scale * 1.005);

      renderer.render(scene, camera);
    };

    animate();

    // Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: newWidth, height: newHeight } = entry.contentRect;
        if (newWidth > 0 && newHeight > 0) {
          camera.aspect = newWidth / newHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(newWidth, newHeight);
        }
      }
    });

    resizeObserver.observe(container);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
      resizeObserver.disconnect();

      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

      // Dispose Geometries & Materials
      [
        coreGeo,
        midGeo,
        outerGeo,
        ring1Geo,
        ring2Geo,
        ring3Geo,
        particleGeo,
      ].forEach((g) => g.dispose());
      [
        coreMat,
        coreWireMat,
        midMat,
        outerMat,
        ring1Mat,
        ring2Mat,
        ring3Mat,
        particleMat,
      ].forEach((m) => m.dispose());
      renderer.dispose();
    };
  }, []);

  return (
    <div
      className="relative w-full border-3 border-[#111111] bg-[#0E1015] shadow-hard-lg overflow-hidden group select-none"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => setPulseCount((c) => c + 1)}
    >
      {/* Background Matrix/Radar Grid */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage:
            "radial-gradient(#B7FF3C 1px, transparent 1px), linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "28px 28px, 56px 56px, 56px 56px",
        }}
      />

      {/* Top Telemetry Header Bar */}
      <div className="relative z-10 flex items-center justify-between px-4 py-3 border-b-2 border-white/15 bg-[#111111]/80 backdrop-blur-md text-[#F5F1E8]">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#B7FF3C] animate-pulse" />
          <span className="font-mono-tech text-xs uppercase font-bold tracking-wider text-white">
            NEURAL_TRUTH_CORE.3D
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono-tech text-[10px] text-[#B7FF3C] uppercase">
          <Activity className="w-3.5 h-3.5" />
          <span>60 FPS • LIVE WEBGL</span>
        </div>
      </div>

      {/* 3D WebGL Canvas Container */}
      <div
        ref={containerRef}
        className="relative w-full h-[360px] sm:h-[420px] flex items-center justify-center cursor-grab active:cursor-grabbing"
      />

      {/* Futuristic HUD Telemetry Overlays */}
      <div className="absolute top-14 left-4 z-10 pointer-events-none space-y-1">
        <div className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-[#111111]/80 border border-[#B7FF3C]/40 text-[#B7FF3C] font-mono-tech text-[10px] font-bold">
          <Cpu className="w-3 h-3" />
          <span>REAL-TIME MULTIMODAL SYNAPSE</span>
        </div>
        <div className="text-[10px] font-mono-tech text-white/50 block pl-0.5">
          POLYGONS: 1,420 • COGNITIVE NODES: 380
        </div>
      </div>

      <div className="absolute bottom-4 left-4 z-10 pointer-events-none">
        <div className="p-2 bg-[#111111]/85 border border-white/20 font-mono-tech text-[10px] text-white/80 space-y-0.5">
          <div className="text-[#B7FF3C] font-bold flex items-center gap-1">
            <Shield className="w-3 h-3" />
            <span>INTELLIGENCE RADAR ACTIVE</span>
          </div>
          <div className="text-[9px] text-white/50">
            INTERACTION: DRAG OR MOVE CURSOR TO ORBIT
          </div>
        </div>
      </div>

      {/* Floating TruthScan Stamp Badge */}
      <div className="absolute -bottom-1 -right-1 z-10 bg-[#B7FF3C] text-[#111111] border-2 border-[#111111] shadow-hard font-display text-xs uppercase px-3 py-1.5 font-bold tracking-wider flex items-center gap-1.5 transform hover:scale-105 transition-transform cursor-pointer">
        <Sparkles className="w-3.5 h-3.5" />
        <span>AUDITED 3D ENGINE</span>
      </div>
    </div>
  );
}
