import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, RoundedBox, Html, Environment, ContactShadows, useGLTF } from '@react-three/drei'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'

type Agent = {
  name: string
  avatar: string
  dept: 'Marketing' | 'Sales' | 'Engineering' | 'Orchestration'
}

function Walls() {
  return (
    <group>
      {/* Back wall */}
      <mesh position={[0, 2.5, -5]} receiveShadow>
        <planeGeometry args={[14, 6]} />
        <meshStandardMaterial color="#ffffff" roughness={0.95} />
      </mesh>
      {/* Left wall */}
      <mesh position={[-7, 2.5, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[10, 6]} />
        <meshStandardMaterial color="#f7f7fb" roughness={0.95} />
      </mesh>
      {/* Right wall with two windows */}
      <group>
        <mesh position={[7, 2.5, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
          <planeGeometry args={[10, 6]} />
          <meshStandardMaterial color="#fafafd" roughness={0.95} />
        </mesh>
        <mesh position={[6.99, 3.2, -1.5]} rotation={[0, -Math.PI / 2, 0]}> 
          <planeGeometry args={[3.2, 1.6]} />
          <meshStandardMaterial color="#eaf2ff" emissive="#eaf2ff" emissiveIntensity={0.5} />
        </mesh>
        <mesh position={[6.99, 2.2, 1.6]} rotation={[0, -Math.PI / 2, 0]}> 
          <planeGeometry args={[2.6, 1.4]} />
          <meshStandardMaterial color="#eaf2ff" emissive="#eaf2ff" emissiveIntensity={0.35} />
        </mesh>
      </group>
      {/* Baseboards */}
      <mesh position={[0, 0.1, -5]}>
        <boxGeometry args={[14, 0.2, 0.1]} />
        <meshStandardMaterial color="#e5e7ef" />
      </mesh>
      <mesh position={[-7, 0.1, 0]} rotation={[0, Math.PI / 2, 0]}>
        <boxGeometry args={[10, 0.2, 0.1]} />
        <meshStandardMaterial color="#e5e7ef" />
      </mesh>
      <mesh position={[7, 0.1, 0]} rotation={[0, Math.PI / 2, 0]}>
        <boxGeometry args={[10, 0.2, 0.1]} />
        <meshStandardMaterial color="#e5e7ef" />
      </mesh>
    </group>
  )
}

function CeilingLights() {
  return (
    <group position={[0, 5.5, 0]}>
      {[-3, 0, 3].map((x) => (
        <mesh key={x} position={[x, 0, 0]}>
          <boxGeometry args={[2.6, 0.04, 0.8]} />
          <meshStandardMaterial color="#ffffff" emissive="#f5f7ff" emissiveIntensity={0.7} />
        </mesh>
      ))}
    </group>
  )
}

function Plant({ position = [0, 0, 0] as [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.18, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.14, 0.22, 16]} />
        <meshStandardMaterial color="#d1d5e1" />
      </mesh>
      <mesh position={[0, 0.42, 0]} castShadow>
        <coneGeometry args={[0.26, 0.5, 12]} />
        <meshStandardMaterial color="#7fb48a" roughness={0.8} />
      </mesh>
    </group>
  )
}

// chairs removed

function Monitor({ position = [0, 0, 0] as [number, number, number] }) {
  return (
    <group position={position}>
      <RoundedBox args={[0.7, 0.42, 0.05]} radius={0.02} position={[0, 0.45, -0.45]} castShadow>
        <meshStandardMaterial color="#111827" />
      </RoundedBox>
      <mesh position={[0, 0.2, -0.45]} castShadow>
        <cylinderGeometry args={[0.03, 0.03, 0.4, 12]} />
        <meshStandardMaterial color="#9aa1b4" />
      </mesh>
      <RoundedBox args={[0.2, 0.04, 0.3]} radius={0.02} position={[0, 0.02, -0.45]}>
        <meshStandardMaterial color="#c7ccd8" />
      </RoundedBox>
    </group>
  )
}

function Laptop({ position = [0, 0, 0] as [number, number, number] }) {
  return (
    <group position={position}>
      <RoundedBox args={[0.28, 0.02, 0.2]} radius={0.01} position={[0, 0.02, 0]}>
        <meshStandardMaterial color="#d6dae6" />
      </RoundedBox>
      <RoundedBox args={[0.28, 0.16, 0.01]} radius={0.01} position={[0, 0.12, -0.09]} rotation={[Math.PI / 2.4, 0, 0]}>
        <meshStandardMaterial color="#1f2937" />
      </RoundedBox>
    </group>
  )
}

function Keyboard({ position = [0, 0, 0] as [number, number, number] }) {
  return (
    <group position={position}>
      <RoundedBox args={[0.28, 0.02, 0.08]} radius={0.01}>
        <meshStandardMaterial color="#e5e7ef" />
      </RoundedBox>
    </group>
  )
}

function CoffeeCup({ position = [0, 0, 0] as [number, number, number] }) {
  return (
    <group position={position}>
      <mesh castShadow>
        <cylinderGeometry args={[0.04, 0.04, 0.08, 16]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
      <mesh position={[0.05, 0.02, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.025, 0.01, 8, 16]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
    </group>
  )
}

function Desk({ position = [0, 0.4, 0] as [number, number, number], rotationY = 0, rugColor = '#ececf4', monitorOffsetX = 0.5 }: { position?: [number, number, number]; rotationY?: number; rugColor?: string; monitorOffsetX?: number }) {
  return (
    <group position={position} rotation={[0, rotationY, 0]}>
      {/* Rug */}
      <RoundedBox args={[3.2, 0.02, 2]} radius={0.02} position={[0, -0.21, 0]}>
        <meshStandardMaterial color={rugColor} roughness={1} />
      </RoundedBox>

      {/* Top */}
      <RoundedBox args={[2.6, 0.2, 1.4]} radius={0.04} position={[0, 0, 0]} castShadow receiveShadow>
        <meshStandardMaterial color="#ffffff" />
      </RoundedBox>
      {/* Plinth */}
      <RoundedBox args={[2.7, 0.1, 1.5]} radius={0.04} position={[0, -0.15, 0]} receiveShadow>
        <meshStandardMaterial color="#dfe3ea" />
      </RoundedBox>
      {/* Legs */}
      {[-1, 1].flatMap((ix) =>
        [-1, 1].map((iz) => (
          <mesh key={`${ix}-${iz}`} position={[ix * 1.1, -0.3, iz * 0.55]} castShadow>
            <cylinderGeometry args={[0.05, 0.05, 0.5, 12]} />
            <meshStandardMaterial color="#b6bccf" />
          </mesh>
        ))
      )}
      {/* Accessories */}
      <Monitor position={[monitorOffsetX, 0, 0.2]} />
      <Laptop position={[-0.4, 0, 0.2]} />
      <Keyboard position={[monitorOffsetX - 0.15, 0.02, -0.05]} />
      <CoffeeCup position={[-0.9, 0.05, -0.2]} />
    </group>
  )
}

// Walker avatar with pause at end before returning
function WalkerAvatar({ url, points, duration = 10, offset = 0, scale = 0.7, dwell = 3, endLabel }: { url: string; points: THREE.Vector3[]; duration?: number; offset?: number; scale?: number; dwell?: number; endLabel?: string }) {
  const { scene } = useGLTF(url) as unknown as { scene: THREE.Group }
  const ref = useRef<THREE.Group>(null)

  const curve = useMemo(() => new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.15), [points])
  const endPoint = points[points.length - 1]

  useMemo(() => {
    scene.traverse((obj: THREE.Object3D) => {
      const o = obj as THREE.Object3D & { castShadow: boolean; receiveShadow: boolean }
      o.castShadow = true
      o.receiveShadow = true
    })
  }, [scene])

  useFrame(({ clock }) => {
    if (!ref.current) return
    const leg = duration
    const cycle = leg + dwell + leg + dwell // forward, dwell, back, dwell
    const raw = (clock.getElapsedTime() + offset) % cycle

    let tt: number
    if (raw < leg) {
      // forward 0->1
      tt = raw / leg
    } else if (raw < leg + dwell) {
      tt = 1
    } else if (raw < leg + dwell + leg) {
      // back 1->0
      tt = 1 - (raw - leg - dwell) / leg
    } else {
      tt = 0
    }

    const pos = curve.getPointAt(tt)
    const ahead = curve.getPointAt(Math.min(1, tt + 0.002))
    ref.current.position.copy(pos)
    ref.current.lookAt(ahead.x, pos.y, ahead.z)

    // Walk bob and sway only while moving
    const moving = !(raw >= leg && raw < leg + dwell) && !(raw >= leg + dwell + leg && raw < cycle)
    if (moving) {
      const step = Math.sin((tt + offset) * Math.PI * 6)
      ref.current.position.y = pos.y + step * 0.02
      ref.current.rotation.z = Math.sin((tt + offset) * Math.PI * 3) * 0.05
    } else {
      ref.current.position.y = pos.y
      ref.current.rotation.z = 0
    }
  })

  const showDialog = (time: number) => {
    const leg = duration
    const cycle = leg + dwell + leg + dwell
    const raw = (time + offset) % cycle
    return raw >= leg && raw < leg + dwell
  }

  return (
    <group>
      <group ref={ref} scale={scale}>
        <primitive object={scene} />
      </group>
      <Html position={[endPoint.x, endPoint.y + 0.6, endPoint.z]} center>
        {/* Dialog visible only during dwell at end */}
        <TimeSyncedDialog visibleFor={(t) => showDialog(t)} label={endLabel ?? 'Quick sync'} />
      </Html>
    </group>
  )
}

// Small helper to show/hide dialog bubble synced to global time
function TimeSyncedDialog({ visibleFor, label }: { visibleFor: (t: number) => boolean; label: string }) {
  const visibleRef = useRef(false)
  useFrame(({ clock }) => {
    visibleRef.current = visibleFor(clock.getElapsedTime())
  })
  // Using inline style to hide without unmount flicker
  return (
    <div style={{ display: visibleRef.current ? 'block' : 'none' }} className="px-3 py-2 rounded-lg bg-white/95 border border-neutral-200 shadow text-xs text-neutral-700">
      {label}
    </div>
  )
}

// Simple seated avatar at a desk
function SeatedAvatar({ url, position = [0, 0, 0.85] as [number, number, number], rotationY = Math.PI, scale = 0.7 }: { url: string; position?: [number, number, number]; rotationY?: number; scale?: number }) {
  const { scene } = useGLTF(url) as unknown as { scene: THREE.Group }
  const ref = useRef<THREE.Group>(null)

  useMemo(() => {
    scene.traverse((obj: THREE.Object3D) => {
      const o = obj as THREE.Object3D & { castShadow: boolean; receiveShadow: boolean }
      o.castShadow = true
      o.receiveShadow = true
    })
  }, [scene])

  return (
    <group ref={ref} position={position} rotation={[0, rotationY, 0]} scale={scale}>
      <primitive object={scene} />
    </group>
  )
}

// Preload seated models
useGLTF.preload('/models/Alfred.glb')
useGLTF.preload('/models/Edith.glb')
useGLTF.preload('/models/Jarvis.glb')

function Whiteboard() {
  return (
    <group>
      <RoundedBox args={[4, 2.2, 0.06]} radius={0.03} position={[0, 3.2, -4.98]}>
        <meshStandardMaterial color="#f9fafb" />
      </RoundedBox>
      <mesh position={[0, 3.2, -4.95]}>
        <boxGeometry args={[4.2, 2.4, 0.02]} />
        <meshStandardMaterial color="#d1d5e1" />
      </mesh>
    </group>
  )
}

function WallArt() {
  return (
    <group>
      <RoundedBox args={[1.1, 1.4, 0.04]} radius={0.02} position={[-6.96, 3.4, -1.2]} rotation={[0, Math.PI / 2, 0]}>
        <meshStandardMaterial color="#e8e0ff" />
      </RoundedBox>
      <RoundedBox args={[1.1, 1.4, 0.04]} radius={0.02} position={[-6.96, 2.1, 1.2]} rotation={[0, Math.PI / 2, 0]}>
        <meshStandardMaterial color="#ffe2d5" />
      </RoundedBox>
    </group>
  )
}

function StorageCabinet() {
  return (
    <group position={[0, 0.45, -4.6]}>
      <RoundedBox args={[3.6, 0.9, 0.5]} radius={0.04}>
        <meshStandardMaterial color="#f2f3f7" />
      </RoundedBox>
      {/* doors */}
      {[-0.9, 0, 0.9].map((x) => (
        <RoundedBox key={x} args={[1.0, 0.86, 0.02]} radius={0.01} position={[x, 0, 0.26]}>
          <meshStandardMaterial color="#e6e8f0" />
        </RoundedBox>
      ))}
    </group>
  )
}

export function Office3D({ agents }: { agents: Agent[] }) {
  useMemo(() => agents, [agents])

  const desks = useMemo(() => ([
    { dept: 'Marketing' as const, position: [-2.2, 0.4, -1.5] as [number, number, number], model: '/models/MJ.glb', rotationY: 0.03, rug: '#eef2ff', monitorX: 0.4 },
    { dept: 'Sales' as const, position: [2.2, 0.4, -1.5] as [number, number, number], model: '/models/Alfred.glb', rotationY: -0.02, rug: '#f4ecec', monitorX: 0.6 },
    { dept: 'Engineering' as const, position: [-2.2, 0.4, 1.5] as [number, number, number], model: '/models/Edith.glb', rotationY: 0.01, rug: '#ecf4ef', monitorX: 0.5 },
    { dept: 'Orchestration' as const, position: [2.2, 0.4, 1.5] as [number, number, number], model: '/models/Jarvis.glb', rotationY: -0.015, rug: '#ececf4', monitorX: 0.55 },
  ]), [])

  const deskMap = useMemo(() => {
    const m = new Map<string, THREE.Vector3>()
    desks.forEach((d) => m.set(d.dept, new THREE.Vector3(...d.position)))
    return m
  }, [desks])

  const mjPathPoints = useMemo(() => {
    const m = deskMap.get('Marketing')!
    const e = deskMap.get('Engineering')!
    const h = 0.02
    const front = (p: THREE.Vector3) => p.clone().add(new THREE.Vector3(0, h, 1.7))
    const leftX = m.x - 2.1
    const start = front(m)
    const p1 = new THREE.Vector3(leftX, h, start.z)
    const midZ = (m.z + e.z) / 2
    const p2 = new THREE.Vector3(leftX, h, midZ)
    const p3 = new THREE.Vector3(leftX, h, e.z - 1.6)
    const p4 = new THREE.Vector3(leftX, h, e.z + 1.3)
    const end = front(e)
    return [start, p1, p2, p3, p4, end]
  }, [deskMap])

  // no additional helpers needed here

  return (
    <Canvas camera={{ position: [0, 4.8, 8.6], fov: 45 }} shadows>
      <fog attach="fog" args={["#eef1f7", 10, 35]} />
      <color attach="background" args={[0.97, 0.98, 1]} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[7, 6, 2]} intensity={1} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
      <directionalLight position={[0, 7, 0]} intensity={0.35} />

      <Walls />
      <CeilingLights />
      <Whiteboard />
      <WallArt />
      <StorageCabinet />
      {/* Soft ceiling spot lights for ambience */}
      <spotLight position={[-3, 6, 2]} angle={0.8} penumbra={0.6} intensity={0.6} color={'#ffffff'} castShadow />
      <spotLight position={[3, 6, -2]} angle={0.8} penumbra={0.6} intensity={0.6} color={'#ffffff'} castShadow />

      {/* Matte carpeted floor */}
      <mesh rotation-x={-Math.PI / 2} receiveShadow position={[0, 0, 0]}>
        <planeGeometry args={[40, 40]} />
        <meshStandardMaterial color="#f2f3f7" roughness={1} metalness={0} />
      </mesh>

      {/* Desks */}
      {desks.map((desk) => (
        <group key={desk.dept} position={desk.position}>
          <Desk rotationY={desk.rotationY} rugColor={desk.rug} monitorOffsetX={desk.monitorX} />
          {/* Seat avatars for Sales, Engineering, Orchestration only */}
          {desk.dept !== 'Marketing' && (
            <SeatedAvatar url={desk.model} />
          )}
          <Html position={[0, 1.1, -0.9]} center>
            <div className="text-xs text-neutral-600">{desk.dept}</div>
          </Html>
        </group>
      ))}

      {/* Single walker: MJ to Edith around desks, pause 3s, walk back */}
      <WalkerAvatar key="mj-edith" url="/models/MJ.glb" points={mjPathPoints} duration={8} dwell={3} offset={0} endLabel="Syncing with Edith" />

      {/* Plants */}
      <Plant position={[-5.8, 0, -3.6]} />
      <Plant position={[5.6, 0, 3.4]} />

      <ContactShadows position={[0, 0.01, 0]} opacity={0.25} scale={20} blur={2} far={5} />
      <Environment preset="city" />
      <OrbitControls enablePan={false} maxPolarAngle={Math.PI / 2.2} minDistance={6} maxDistance={14} />
    </Canvas>
  )
} 