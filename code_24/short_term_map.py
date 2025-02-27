import numpy as np
from collections import deque

class ShortTermMap:
    def __init__(self, max_distance=0.5):
        """
        max_distance: how far you will allow the car to travel before discarding old scans
        """
        self.max_distance = max_distance
        # Each entry in the buffer will be (scan_data, x_pose, y_pose, heading)
        # where scan_data is a 1D array of size 360 with distances
        self.ring_buffer = deque()
        # We’ll also keep track of the pose at time of last update
        self.current_pose = (0.0, 0.0, 0.0)  # (x, y, heading)

    def update_pose(self, x, y, heading):
        """Call this with the current estimated pose from encoders/odometry."""
        self.current_pose = (x, y, heading)

    def add_scan(self, scan_data):
        """
        Add the new LiDAR scan to the ring buffer, 
        along with the current pose at which it was taken.
        """
        self.ring_buffer.append((scan_data.copy(), *self.current_pose))

    def prune_old_scans(self):
        """
        Remove scans that are older than `max_distance` of travel away
        from our current pose.
        """
        x_now, y_now, _ = self.current_pose
        while self.ring_buffer:
            # Check the oldest scan
            scan_data, x_then, y_then, heading_then = self.ring_buffer[0]
            dist_traveled = np.hypot(x_now - x_then, y_now - y_then)
            if dist_traveled > self.max_distance:
                # This scan is too far behind us -> discard
                self.ring_buffer.popleft()
            else:
                break

    def build_composite_scan(self):
        """
        Combine all the scans in the buffer (including the newest).
        Transform them into the current frame, and 
        take the minimum distance at each angle, for instance.

        Returns a 360-sized array of "remembered distances."
        """
        x_now, y_now, heading_now = self.current_pose

        # Start with "infinite" (or zero) distances
        # If you prefer 0 means "unknown," you can invert logic below.
        remembered = np.full(360, np.inf)

        for scan_data, x_then, y_then, heading_then in self.ring_buffer:
            dx = x_now - x_then
            dy = y_now - y_then
            d_heading = heading_now - heading_then

            # For each angle i, we have scan_data[i].
            # We must transform that point from the old pose into the current pose.
            # A naive approach: For each i in [0..359], convert to (x_old, y_old),
            # then transform by (dx, dy, d_heading) into the current frame,
            # then convert back to polar. Then we figure out the new angle bin
            # and distance. Finally, we do "remembered[new_angle_bin] = min(...)"
            # for collisions. 
            
            # For brevity, just show the idea in code comments:

            angles_rad = np.deg2rad(np.arange(360))
            old_r = scan_data
            # Cartesian in old frame (relative to old LIDAR center)
            x_local_old = old_r * np.cos(angles_rad)
            y_local_old = old_r * np.sin(angles_rad)
            
            # Now shift by old vehicle pose w.r.t. current pose.
            # 1) rotate by d_heading
            cosH = np.cos(d_heading)
            sinH = np.sin(d_heading)

            # Because we want to see how the old points appear *in the current frame*,
            # we apply first the old->world transform, then world->current transform.
            # A simpler method if you only have small heading changes is this "relative" approach:
            #   x_world = x_then + x_local_old
            #   y_world = y_then + y_local_old
            #   x_local_new = x_world - x_now
            #   y_local_new = y_world - y_now
            #
            # Then rotate by -heading_now or something similar. 
            #
            # A more direct approach is: 
            #   x_local_new = cos(d_heading)*x_local_old - sin(d_heading)*y_local_old + dx_local
            #   y_local_new = sin(d_heading)*x_local_old + cos(d_heading)*y_local_old + dy_local
            #
            # where dx_local, dy_local is the offset in the old->new local frame.

            # For a short example, assume we do a pure "relative transform":

            # Convert old local -> global
            x_global = x_then + x_local_old
            y_global = y_then + y_local_old
            
            # Then global -> current local
            x_local = (x_global - x_now)*np.cos(-heading_now) - (y_global - y_now)*np.sin(-heading_now)
            y_local = (x_global - x_now)*np.sin(-heading_now) + (y_global - y_now)*np.cos(-heading_now)

            # Now compute distance and angle in the current frame
            new_r = np.hypot(x_local, y_local)
            new_angles = np.arctan2(y_local, x_local)  # range -pi..pi
            # Convert angles to [0..360)
            new_angle_deg = np.rad2deg(new_angles) % 360
            # Round to nearest integer bin
            new_bins = np.round(new_angle_deg).astype(int) % 360

            # Update the remembered distance with the min (assuming obstacles).
            for bin_i, dist_i in zip(new_bins, new_r):
                if dist_i < remembered[bin_i]:
                    remembered[bin_i] = dist_i

        # If you prefer to store 0 for “no reading,” you can invert:
        remembered = np.where(np.isinf(remembered), 0.0, remembered)
        return remembered
