# app/themes_data.py

THEMES = {
    "salud": {
        "title": "Desafíos — Salud",
        "hero": "Mejora hábitos y bienestar en tu comunidad.",
        "chips": ["🫶 Empatía", "💪 Bienestar", "💡 Innovación"],
        "accent": "#22c55e",
        "image": "images/salud.webp",
        "challenges": [
            {
                "id": 1,
                "name": "Autogestión de tratamientos",
                "summary": "Mejora la adherencia a tratamientos médicos en pacientes crónicos.",
                "desc": "Muchos errores médicos y complicaciones surgen al cambiar de un centro de salud a otro, "
                "por falta de continuidad y seguimiento personalizado. Don Humberto de 50 años, fue dado de alta con indicaciones médicas complejas, pero no entendió qué debía seguir "
                "tomando ni a quién acudir si se sentía mal."
            },
            {
                "id": 2,
                "name": "Obesidad",
                "summary": "Aborda el sobrepeso y la obesidad mediante educación y hábitos saludables.",
                "desc": "Más de un 70% de la población en Chile presenta sobrepeso u obesidad (MINSAL). Esta situación se debe a múltiples factores, entre ellos la falta de ejercicio y educación "
                "nutricional, disponibilidad de productos ultraprocesados y la desinformación. Simona "
                "tiene 27 años, una hija pequeña y trabaja tiempo completo. Sabe que la alimentación es "
                "clave, pero no ha podido organizar ni aprender a darle una nutrición buena a su hija."
            },
            {
                "id": 3,
                "name": "Envejecimiento activo",
                "summary": "Fomenta la actividad y socialización en adultos mayores para un envejecimiento saludable.",
                "desc": "La población chilena está envejeciendo rápidamente y muchos adultos mayores enfrentan "
                "soledad, pérdida de movilidad y falta de programas de prevención. Juana, de 72 años, vive "
                "sola desde que sus hijos se independizaron. Le gustaría mantenerse activa, pero no "
                "conoce programas accesibles que la motiven a hacer ejercicio, socializar y prevenir "
                "enfermedades."

            },
        ],
    },
    "sustentabilidad": {
        "title": "Desafíos — Sustentabilidad",
        "hero": "Crea impacto ambiental positivo y medible.",
        "chips": ["🌱 Ambiental", "♻️ Circular", "⚙️ Creativo"],
        "accent": "#16a34a",
        "image": "images/sustentabilidad.webp",
        "challenges": [
            {
                "id": 1,
                "name": "Contaminación por fast fashion",
                "summary": "Impacto ambiental negativo de la moda rápida en comunidades vulnerables.",
                "desc": "La moda rápida ha traído graves consecuencias al medio ambiente. Especialmente en "
                "sectores del norte de Chile en donde los vertederos y basurales están afectando el diario "
                "vivir de las personas. Gabriela es una estudiante de 18 años que vive cerca de esta zona y "
                "debe pasar a diario por lugares con desagradables olores."
            },
            {
                "id": 2,
                "name": "Acceso al agua en la agricultura",
                "summary": "Escasez de agua dulce en zonas rurales afecta la agricultura.",
                "desc": "El agua dulce es un recurso natural fundamental para la vida. Hay zonas rurales en que el "
                "agua se ha hecho escasa. Camila es una agricultora de 50 años que cultiva paltas de "
                "exportación, ella está complicada de perder su negocio por la cantidad de agua que debe "
                "utilizar."
            },
            {
                "id": 3,
                "name": "Gestión de residuos electrónicos",
                "summary": "Dificultades en el reciclaje de desechos electrónicos a nivel masivo.",
                "desc": "El aumento del consumo tecnológico ha generado toneladas de desechos electrónicos "
                "difíciles de reciclar. Francisco, de 29 años, cambió su celular y computador el año pasado, "
                "pero no sabe dónde llevar los antiguos dispositivos. Terminó guardándolos en un cajón, "
                "como millones de personas que desconocen alternativas de reciclaje."

            },
        ],
    },
    "educacion": {
        "title": "Desafíos — Educación",
        "hero": "Mejora la experiencia de aprendizaje e inclusión.",
        "chips": ["🗣️ Comunicar", "🎓 Liderazgo", "💭 Ideas"],
        "accent": "#3b82f6",
        "image": "images/educacion.webp",
        "challenges": [
            {
                "id": 1,
                "name": "Educación financiera accesible", 
                "summary": "La ausencia de educación financiera en realidades económicas inestables.",
                "desc": "La ausencia de educación financiera en realidades económicas inestables dificulta la "
                "planificación y el uso responsable del dinero. Martina, joven emprendedora de 22 años, "
                "vende productos por redes sociales. Aunque gana dinero, no sabe cómo organizarlo ni "
                "cuánto debe ahorrar o invertir, lo que la mantiene en constante inestabilidad."
            },
            {
                "id": 2,
                "name": "Inicio de vida laboral",
                "summary": "Barreras para conseguir el primer empleo debido a la falta de experiencia previa.",
                "desc": "Muchos estudiantes recién titulados enfrentan barreras para conseguir su primer empleo, "
                "ya que se les exige experiencia previa que aún no han podido adquirir. Andrés, de 23 años, "
                "acaba de egresar de odontología. Le preocupa no poder trabajar pronto, pero ninguna "
                "clínica lo ha llamado porque no tiene experiencia previa."
            },
            {
                "id": 3,
                "name": "Tecnología adultos mayores",
                "summary": "Dificultades de los adultos mayores para adaptarse a la tecnología en trámites diarios.",
                "desc": "El avance tecnológico en los últimos años ha sido incremental. Esto ha beneficiado a "
                "múltiples sectores, sin embargo el conocimiento y adaptación para los adultos mayores ha "
                "sido una gran dificultad. Osvaldo es un adulto mayor de 70 años y debe pedir ayuda a sus "
                "hijos o nietos cada vez que debe hacer trámites."

            },
        ],
    },
}

def get_theme(slug):
    return THEMES.get(slug.lower())
