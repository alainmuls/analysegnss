#include <stdio.h>
#include <math.h>

// WGS 84 constants
#define GM_EARTH 3.986005e14    // Earth's gravitational constant [m^3/s^2]
#define OMEGA_E 7.2921151467e-5 // Earth's rotation rate [rad/s]

typedef struct
{
    double toe;       // Time of ephemeris
    double sqrta;     // Square root of semi-major axis
    double e;         // Eccentricity
    double i0;        // Inclination at reference time
    double omega;     // Argument of perigee
    double Omega0;    // Right ascension at reference time
    double M0;        // Mean anomaly at reference time
    double delta_n;   // Mean motion correction
    double Omega_dot; // Rate of right ascension
    double idot;      // Rate of inclination
    double cuc, cus;  // Latitude correction terms
    double crc, crs;  // Radius correction terms
    double cic, cis;  // Inclination correction terms
} broadcast_ephemeris_t;

void calc_satellite_position(broadcast_ephemeris_t *eph, double t,
                             double *x, double *y, double *z)
{
    // Time from ephemeris reference epoch
    double tk = t - eph->toe;

    // Compute mean motion
    double a = eph->sqrta * eph->sqrta;
    double n0 = sqrt(GM_EARTH / (a * a * a));
    double n = n0 + eph->delta_n;

    // Mean anomaly
    double M = eph->M0 + n * tk;

    // Solve Kepler's equation iteratively
    double E = M;
    double E_old;
    for (int i = 0; i < 10; i++)
    {
        E_old = E;
        E = M + eph->e * sin(E);
        if (fabs(E - E_old) < 1e-12)
            break;
    }

    // True anomaly
    double cos_E = cos(E);
    double sin_E = sin(E);
    double nu = atan2(sqrt(1 - eph->e * eph->e) * sin_E, cos_E - eph->e);

    // Argument of latitude
    double phi = nu + eph->omega;

    // Second harmonic perturbations
    double sin_2phi = sin(2 * phi);
    double cos_2phi = cos(2 * phi);

    double du = eph->cuc * cos_2phi + eph->cus * sin_2phi; // Latitude correction
    double dr = eph->crc * cos_2phi + eph->crs * sin_2phi; // Radius correction
    double di = eph->cic * cos_2phi + eph->cis * sin_2phi; // Inclination correction

    // Corrected argument of latitude, radius and inclination
    double u = phi + du;
    double r = a * (1 - eph->e * cos_E) + dr;
    double i = eph->i0 + di + eph->idot * tk;

    // Positions in orbital plane
    double x_op = r * cos(u);
    double y_op = r * sin(u);

    // Corrected longitude of ascending node
    double Omega = eph->Omega0 + (eph->Omega_dot - OMEGA_E) * tk - OMEGA_E * eph->toe;

    // Earth-fixed coordinates
    *x = x_op * cos(Omega) - y_op * cos(i) * sin(Omega);
    *y = x_op * sin(Omega) + y_op * cos(i) * cos(Omega);
    *z = y_op * sin(i);
}

int main()
{
    broadcast_ephemeris_t eph = {
        .toe = 0.0,
        .sqrta = 5153.79589081,
        .e = 0.00223578442819,
        .i0 = 0.961685061380,
        // ... add remaining ephemeris parameters
    };

    double x, y, z;
    double t = 3600; // 1 hour from toe

    calc_satellite_position(&eph, t, &x, &y, &z);
    printf("Satellite position (ECEF):\n");
    printf("X: %.3f m\n", x);
    printf("Y: %.3f m\n", y);
    printf("Z: %.3f m\n", z);

    return 0;
}
