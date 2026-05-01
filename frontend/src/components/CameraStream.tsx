/**
 * Live camera feed rendered as the global app background. The browser handles
 * the MJPEG stream natively via <img>; we just style it to fill the viewport.
 */
export function CameraStream() {
  return (
    <img
      src="/stream.mjpg"
      alt=""
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        pointerEvents: 'none',
        userSelect: 'none',
        zIndex: 0,
      }}
    />
  )
}
