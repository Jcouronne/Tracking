#include <Servo.h>

// --- Broches de connexion des Servomoteurs ---
#define PIN_PAN_SERVO 5   // Moteur Horizontal (Pan)
#define PIN_TILT_SERVO 6 // Moteur Vertical (Tilt)

Servo pan_servo; 
Servo tilt_servo;

// --- Angles de Contrôle (État Actuel) ---
int current_pan_angle = 90; 
int current_tilt_angle = 90;

// Plage maximale des angles (Sécurité mécanique)
const int MIN_ANGLE = 45; 
const int MAX_ANGLE = 135; 
const int CENTER_ANGLE = 90;

// Communication Série
const int BAUDRATE = 9600; // DOIT CORRESPONDRE AU CODE PYTHON

void setup() {
    pan_servo.attach(PIN_PAN_SERVO);
    tilt_servo.attach(PIN_TILT_SERVO);

    // Position initiale : placer les moteurs au centre
    pan_servo.write(CENTER_ANGLE);
    tilt_servo.write(CENTER_ANGLE);

    Serial.begin(BAUDRATE);
    Serial.println("Tourelle prete. Attente de commandes...");
}

void loop() {
    // S'assurer qu'au moins une ligne complète est disponible
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');

        // --- Traitement de la commande PAN ---
        if (command.startsWith("PAN:")) {
            // Extraire le pas (step) : ex: "-5" à partir de "PAN:-5"
            int step = command.substring(4).toInt();

            // Calcul du nouvel angle : Ajout du pas (qui peut être positif ou négatif)
            int new_angle = current_pan_angle + step;

            // Sécurité: Limiter le nouvel angle
            new_angle = constrain(new_angle, MIN_ANGLE, MAX_ANGLE);

            // Mise à jour de l'état et commande
            current_pan_angle = new_angle;
            pan_servo.write(current_pan_angle);

            // Optionnel: Décommenter pour visualiser les angles dans le Moniteur Série
            // Serial.print("PAN: Step="); Serial.print(step); Serial.print(", Angle="); Serial.println(current_pan_angle);
        } 
        // --- Traitement de la commande TILT ---
        else if (command.startsWith("TILT:")) {
            // Extraire le pas (step) : ex: "2" à partir de "TILT:2"
            int step = command.substring(5).toInt();

            // Calcul du nouvel angle
            int new_angle = current_tilt_angle + step;

            // Sécurité: Limiter le nouvel angle
            new_angle = constrain(new_angle, MIN_ANGLE, MAX_ANGLE);

            // Mise à jour de l'état et commande
            current_tilt_angle = new_angle;
            tilt_servo.write(current_tilt_angle);

            // Optionnel: Décommenter pour visualiser les angles dans le Moniteur Série
            // Serial.print("TILT: Step="); Serial.print(step); Serial.print(", Angle="); Serial.println(current_tilt_angle);
        }
    }
}
