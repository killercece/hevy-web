# Notes de Design - Clone Web Hevy

## Palette officielle (extraite de `colors.xml`)

- **Accent primaire (Hevy)** : `#267fe8` (bleu signature — pas orange malgré idée recue)
- **Icône Hevy** : `#000000`
- **Fond dark material** : `#121212` (standard Material Design)
- **Surface dark** : `#1E1E1E` / `#1A1A1A`

## Palette du clone web (variables CSS)

```css
--bg-primary: #0E0E0E;     /* fond principal */
--bg-secondary: #1A1A1A;   /* cartes, surfaces */
--bg-tertiary: #242424;    /* inputs, éléments elevés */
--bg-elevated: #2A2A2A;    /* modals, menus */

--accent: #267fe8;         /* bleu Hevy */
--accent-hover: #1a6dd0;
--accent-soft: rgba(38, 127, 232, 0.12);

--text-primary: #FFFFFF;
--text-secondary: #AAAAAA;
--text-tertiary: #666666;

--success: #22C55E;        /* check sets completed */
--warning: #F59E0B;         /* PR, achievements */
--error: #EF4444;
--border: #2A2A2A;
--divider: #1F1F1F;
```

## Typographie

- Sans-serif moderne : `Inter` (via Google Fonts CDN), fallback `system-ui`
- Tailles : `12 / 14 / 16 / 18 / 20 / 24 / 32px`
- Poids : `400 / 500 / 600 / 700`

## Layout

- **Mobile-first** (Hevy est une app mobile avant tout)
- Bottom navbar fixe sur mobile (4 onglets : Home / Exercises / Workout / Profile)
- Desktop : sidebar ou top nav
- Contenu max-width desktop : `480px` (feel mobile) ou `1200px` (large pages stats)
- Paddings standard : `16px` bord d'écran, `12px` entre cartes

## Composants clés

### Bouton CTA principal
- Background `--accent`, text blanc, bold
- Border-radius `12px`
- Padding `14px 24px`
- Shadow subtile : `0 4px 12px rgba(38,127,232,0.3)`

### Carte routine / workout
- Background `--bg-secondary`, radius `12px`, padding `16px`
- Titre bold, sous-titre secondary
- Border `1px solid transparent` → hover `--border`

### Input numérique (saisie reps/weight)
- `inputmode="decimal"` pour clavier numérique mobile
- Large touch target (≥44px hauteur)
- Background `--bg-tertiary`, border none focus accent
- Text-align center
- Font-size `18px`

### Ligne de set (workout actif)
```
[Set#] [Previous kg×reps] [kg input] [reps input] [checkbox ✓]
```
- Hauteur `56px`, séparateur divider
- Checkbox completed : fond vert `--success`, icône check blanche
- Set number chip : circle `--bg-tertiary`

### Navbar bottom mobile
- Fond `--bg-secondary` (ou `--bg-primary` avec border-top)
- Height `64px`
- 4 icônes + labels, actif = accent color
- Icônes Lucide (home, dumbbell, plus-circle, user)
- Safe-area bottom padding iOS

### Timer repos modal
- Bottom sheet, slide up
- Countdown large (48px bold)
- Boutons : -15s / +15s / Skip

## Iconographie

- Set **Lucide Icons** via CDN `https://unpkg.com/lucide@latest`
- Icônes clés : `home`, `dumbbell`, `plus`, `user`, `check`, `clock`, `play`, `pause`, `trash-2`, `edit-3`, `copy`, `folder`, `search`, `filter`, `chevron-right`, `chevron-down`, `x`

## Interactions

- Transitions `150ms ease` sur hover/focus
- Press state mobile : `transform: scale(0.98)` + `opacity 0.8`
- Feedback haptique via `navigator.vibrate()` quand supporté
- Sons discret via `<audio>` pour fin timer

## Références

- Site officiel : https://www.hevyapp.com/
- App Store : screenshots officiels
- Resources APK décompilé : `/projects/hevy/src/resources/res/`

## Refonte qualité avril 2026 — principes appliqués

1. **Vidéos d'exercices** : intégration du CDN public Hevy
   (`https://d2l9nsnmtah87f.cloudfront.net/exercise-assets/{id}-{slug}_{muscle}.mp4`).
   Chaque exercice a (quand trouvé) un `cdn_video_id` qui compose une URL
   mp4 publique utilisable en `<video autoplay muted loop playsinline>`.
2. **Matching TSV** : `app/data/hevy_exercises_cdn.tsv` liste ~363 vidéos.
   Un algo de matching fuzzy (normalisation, intersection tokens, exclusion
   variantes `(female)`/`(version-2)`) attache les vidéos aux exercices
   curated et complète la bibliothèque avec les entrées manquantes.
3. **Lazy video loader** : `Hevy.video.scan()` + IntersectionObserver —
   les `<video data-lazy-src="...">` ne sont chargées que quand visibles,
   permettant d'afficher des centaines de vignettes sans saturer le réseau.
4. **Rest timer circulaire** : SVG `stroke-dashoffset` qui décroît, plus
   grosse typo centrale, vibration longue + beep généré via AudioContext
   en fallback quand le mp3 n'est pas disponible.
5. **Grille d'exercices Hevy-like** : `.ex-card` avec aspect-ratio 4/5,
   vidéo en fond, overlay dégradé, nom en bas. Toggle grid/list persistant
   dans localStorage.
6. **Stats row enrichie** : icônes contextuelles discrètes en haut à droite,
   valeurs en 26px bold letter-spacing -0.5, cartes avec border.
7. **Tokens ajoutés** : `--space-10/12/14`, `--radius-2xl`, `--shadow-card`,
   `--shadow-press`, couleurs spécifiques types de sets (warmup jaune,
   drop bleu, failure rouge).
8. **Micro-interactions** : `translateY(-1px)` + shadow au hover des cards,
   `chipPop` à l'activation d'un chip, `checkPop` quand on valide un set.
9. **Bottom nav mobile** : `backdrop-filter: blur(12px)` + glow léger
   autour de l'icône active.
10. **Historique timeline** : regroupement par date relative (Aujourd'hui,
    Hier, Cette semaine, puis par mois) avec séparateurs visuels, chaque
    card de workout embarque les mini-thumbnails vidéo des 5 premiers
    exercices.

## Points d'attention (UX Hevy)

1. **Saisie fluide** : focus auto sur prochain input après check
2. **Previous** : afficher la dernière perf (kg × reps) à côté de la saisie — motivation clé
3. **Persistence locale** : localStorage pour resilience workout en cours
4. **Timer visible** : chrono session qui tourne en haut, toujours visible
5. **Finish Workout** : CTA fixe en bas, accent color
6. **Feed historique** : cartes par workout, date en relatif ("il y a 2j")
