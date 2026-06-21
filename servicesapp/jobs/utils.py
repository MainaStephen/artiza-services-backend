from geopy.distance import geodesic

def is_within_radius(job_lat, job_lng, worker_lat, worker_lng, radius_km=20):

    # STRICT NULL CHECK (safe for 0.0 values)
    if None in [job_lat, job_lng, worker_lat, worker_lng]:
        return False

    job_location = (job_lat, job_lng)
    worker_location = (worker_lat, worker_lng)

    try:
        distance = geodesic(job_location, worker_location).km
        return distance <= radius_km
    except Exception:
        return False