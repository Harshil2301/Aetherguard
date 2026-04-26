'use client';

import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float, Stars } from '@react-three/drei';
import * as THREE from 'three';

/* ── Full-page fixed star field ── */
export function StarCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0, 1], fov: 75 }}
      style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', pointerEvents: 'none', zIndex: 0 }}
      gl={{ alpha: true, antialias: false }}
    >
      <Stars radius={150} depth={80} count={7000} factor={5} saturation={0.5} fade speed={0.6} />
    </Canvas>
  );
}

/* ── Vivid 3-D planet for hero ── */
function GlowSphere() {
  const outer = useRef(null);
  const inner = useRef(null);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    if (outer.current) { outer.current.rotation.y = t * 0.1; outer.current.rotation.x = Math.sin(t * 0.07) * 0.25; }
    if (inner.current) { inner.current.rotation.y = -t * 0.18; }
  });
  return (
    <Float speed={1.0} floatIntensity={0.5} rotationIntensity={0.15}>
      <Sphere ref={outer} args={[1.55, 128, 128]}>
        <MeshDistortMaterial color="#00e5ff" distort={0.32} speed={1.8} roughness={0.05} metalness={0.95} transparent opacity={0.92} toneMapped={false} />
      </Sphere>
      <Sphere ref={inner} args={[0.98, 64, 64]}>
        <MeshDistortMaterial color="#7c3aed" distort={0.65} speed={2.8} roughness={0} transparent opacity={0.6} toneMapped={false} />
      </Sphere>
    </Float>
  );
}

export function HeroSphereCanvas() {
  return (
    <Canvas camera={{ position: [0, 0, 4.2], fov: 52 }}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
      gl={{ alpha: true, antialias: true }}>
      <ambientLight intensity={0.3} />
      <pointLight position={[4, 4, 4]}   intensity={4} color="#00e5ff" />
      <pointLight position={[-4, -4, -4]} intensity={3} color="#7c3aed" />
      <pointLight position={[0, 6, -6]}   intensity={2} color="#3b82f6" />
      <GlowSphere />
    </Canvas>
  );
}

export default HeroSphereCanvas;
