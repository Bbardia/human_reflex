import { useEffect, useRef } from 'react'
import type { Pose } from '../types'

const SKELETON_EDGES: [number, number][] = [
  [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],
  [5, 11], [6, 12], [11, 12],
  [11, 13], [13, 15], [12, 14], [14, 16],
]

const HEAD_KEYPOINTS = [0, 1, 2, 3, 4]

interface SkeletonProps {
  pose: Pose | null
  /** What region of the full camera frame should be drawn into the canvas? Half-screen for split. */
  fromXMin: number
  fromXMax: number
  color: string
  glowBlur?: number
  width: number
  height: number
}

export function Skeleton({ pose, fromXMin, fromXMax, color, glowBlur = 8, width, height }: SkeletonProps) {
  const ref = useRef<HTMLCanvasElement>(null)

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

    ctx.shadowColor = color
    ctx.shadowBlur = glowBlur
    ctx.strokeStyle = color
    ctx.lineWidth = 4
    ctx.lineCap = 'round'

    // edges
    for (const [a, b] of SKELETON_EDGES) {
      const ka = pose.keypoints[a]
      const kb = pose.keypoints[b]
      if (ka[2] < 0.3 || kb[2] < 0.3) continue
      ctx.beginPath()
      ctx.moveTo(sx(ka[0]), sy(ka[1]))
      ctx.lineTo(sx(kb[0]), sy(kb[1]))
      ctx.stroke()
    }

    // joints
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
