import { useEffect, useRef } from 'react'
import type { Pose } from '../types'

const LEFT_WRIST = 9
const RIGHT_WRIST = 10

const SKELETON_EDGES: [number, number][] = [
  [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],
  [5, 11], [6, 12], [11, 12],
  [11, 13], [13, 15], [12, 14], [14, 16],
]

const HEAD_KEYPOINTS = [0, 1, 2, 3, 4]
const TRAIL_LEN = 8

interface TrailPoint {
  x: number
  y: number
}

interface SkeletonProps {
  pose: Pose | null
  fromXMin: number
  fromXMax: number
  color: string
  glowBlur?: number
  width: number
  height: number
}

export function Skeleton({ pose, fromXMin, fromXMax, color, glowBlur = 8, width, height }: SkeletonProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const leftTrailRef = useRef<TrailPoint[]>([])
  const rightTrailRef = useRef<TrailPoint[]>([])

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, width, height)
    if (!pose) return

    const fromW = fromXMax - fromXMin
    if (fromW <= 0) return
    const sx = (kx: number) => ((kx - fromXMin) / fromW) * width
    const sy = (ky: number) => ky * height

    // Update trails
    const lw = pose.keypoints[LEFT_WRIST]
    if (lw[2] >= 0.3) {
      leftTrailRef.current.push({ x: lw[0], y: lw[1] })
      if (leftTrailRef.current.length > TRAIL_LEN) leftTrailRef.current.shift()
    }
    const rw = pose.keypoints[RIGHT_WRIST]
    if (rw[2] >= 0.3) {
      rightTrailRef.current.push({ x: rw[0], y: rw[1] })
      if (rightTrailRef.current.length > TRAIL_LEN) rightTrailRef.current.shift()
    }

    // Draw trails (oldest=most transparent)
    ctx.shadowColor = color
    ctx.shadowBlur = glowBlur
    for (const trail of [leftTrailRef.current, rightTrailRef.current]) {
      const n = trail.length
      for (let i = 0; i < n; i++) {
        const p = trail[i]
        const alpha = (i + 1) / (n + 1)
        ctx.globalAlpha = alpha * 0.5
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(sx(p.x), sy(p.y), 6 - i * 0.3, 0, Math.PI * 2)
        ctx.fill()
      }
    }
    ctx.globalAlpha = 1.0

    // Skeleton edges
    ctx.strokeStyle = color
    ctx.lineWidth = 4
    ctx.lineCap = 'round'
    for (const [a, b] of SKELETON_EDGES) {
      const ka = pose.keypoints[a]
      const kb = pose.keypoints[b]
      if (ka[2] < 0.3 || kb[2] < 0.3) continue
      ctx.beginPath()
      ctx.moveTo(sx(ka[0]), sy(ka[1]))
      ctx.lineTo(sx(kb[0]), sy(kb[1]))
      ctx.stroke()
    }

    // Joints
    ctx.fillStyle = color
    for (let i = 0; i < pose.keypoints.length; i++) {
      const k = pose.keypoints[i]
      if (k[2] < 0.3) continue
      ctx.beginPath()
      ctx.arc(sx(k[0]), sy(k[1]), HEAD_KEYPOINTS.includes(i) ? 8 : 5, 0, Math.PI * 2)
      ctx.fill()
    }
  }, [pose, fromXMin, fromXMax, color, glowBlur, width, height])

  return <canvas ref={ref} width={width} height={height} style={{ display: 'block' }} />
}
