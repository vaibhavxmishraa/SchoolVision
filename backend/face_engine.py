"""
Face recognition engine with SELF-HEALING fallback.
- Agar face_recognition + opencv installed -> real recognition.
- Warna -> simulated mode (mock 128-d vectors) taaki demo chal jaye.
"""
import json, base64, io, random
import numpy as np

REAL_MODE = True
try:
    import face_recognition  # type: ignore
    import cv2  # type: ignore
except Exception:
    REAL_MODE = False
    print("[FaceEngine] ⚠ face_recognition/opencv not found -> SIMULATED MODE ON.")


def _decode_image(data_url: str):
    """Base64 data URL -> numpy RGB image (only in REAL_MODE)."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    if REAL_MODE:
        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img_bytes


# def get_encodings_from_image(data_url: str):
#     """Returns list of encoding vectors (128-d) found in image."""
#     if REAL_MODE:
#         try:
#             img = _decode_image(data_url)
#             locations = face_recognition.face_locations(img)
#             encs = face_recognition.face_encodings(img, locations)
#             return [e.tolist() for e in encs]
#         except Exception as e:
#             print(f"[FaceEngine] real encode failed: {e}")
#             return []
#     # Simulated: generate a pseudo-stable encoding
#     seed = sum(bytearray(_decode_image(data_url)[:200])) if isinstance(
#         _decode_image(data_url), (bytes, bytearray)) else random.random()
#     rng = np.random.default_rng(int(abs(seed)) % (2**32))
#     return [rng.random(128).tolist()]

def get_encodings_from_image(data_url: str):
    """Returns list of encoding vectors (128-d) found in image."""
    if REAL_MODE:
        try:
            img = _decode_image(data_url)
            locations = face_recognition.face_locations(img)
            encs = face_recognition.face_encodings(img, locations)
            return [e.tolist() for e in encs]
        except Exception as e:
            print(f"[FaceEngine] real encode failed: {e}")
            return []
    # SIMULATED: har scan me random 1-3 "faces" simulate karo (demo ke liye)
    raw = _decode_image(data_url)
    seed = sum(bytearray(raw[:200])) if isinstance(raw, (bytes, bytearray)) else 0
    rng = np.random.default_rng((int(abs(seed)) + random.randint(0, 9999)) % (2**32))
    num_faces = random.randint(1, 3)
    return [rng.random(128).tolist() for _ in range(num_faces)]


def match_face(unknown_enc, students, tolerance=0.5):
    """
    students: list of (student_id, name, encodings_json)
    Returns matched student dict or None.
    """
    if not unknown_enc:
        return None
    unknown = np.array(unknown_enc)
    best_id, best_name, best_dist = None, None, 999.0
    for sid, name, enc_json in students:
        try:
            encs = json.loads(enc_json or "[]")
        except Exception:
            encs = []
        for e in encs:
            dist = float(np.linalg.norm(np.array(e) - unknown))
            if dist < best_dist:
                best_dist, best_id, best_name = dist, sid, name
    if REAL_MODE:
        if best_id is not None and best_dist <= tolerance:
            return {"student_id": best_id, "name": best_name, "distance": round(best_dist, 3)}
        return None
    # Simulated: relaxed threshold so demo shows matches
    if best_id is not None and best_dist <= 6.0:
        return {"student_id": best_id, "name": best_name, "distance": round(best_dist, 3)}
    return None