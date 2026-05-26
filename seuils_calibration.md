# Seuils de calibration — Étudiant 1 Hardware
## Statut : En attente matériel physique (semaine 4)

## MQ-2 (gaz GPL / fumée) — GPIO 34
| Condition | Valeur ADC Wokwi | Valeur ADC Réelle |
|-----------|-----------------|-------------------|
| Air propre | à mesurer | - |
| WARNING | > 1500 | à calibrer |
| DANGER | > 2500 | à calibrer |
| CRITIQUE | > 3500 | à calibrer |

## MQ-7 (monoxyde de carbone) — GPIO 35
| Condition | Valeur ADC Wokwi | Valeur ADC Réelle |
|-----------|-----------------|-------------------|
| Air propre | à mesurer | - |
| Détection CO | > 1500 | à calibrer |

## HC-SR04 (niveau cuve) — GPIO 5/18
| Condition | Valeur cm Wokwi | Valeur cm Réelle |
|-----------|----------------|------------------|
| Cuve vide | 30 cm | à mesurer |
| Cuve pleine | 0 cm | à mesurer |

## Câble de fuite — GPIO 21
| Condition | Valeur |
|-----------|--------|
| Sec | HIGH |
| Mouillé eau salée | LOW |

## Notes
- Valeurs Wokwi = approximatives, non calibrées
- Calibration réelle à faire en semaine 4 avec matériel physique
- Préchauffage MQ-2 requis : 24-48h avant calibration