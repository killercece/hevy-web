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

## Points d'attention (UX Hevy)

1. **Saisie fluide** : focus auto sur prochain input après check
2. **Previous** : afficher la dernière perf (kg × reps) à côté de la saisie — motivation clé
3. **Persistence locale** : localStorage pour resilience workout en cours
4. **Timer visible** : chrono session qui tourne en haut, toujours visible
5. **Finish Workout** : CTA fixe en bas, accent color
6. **Feed historique** : cartes par workout, date en relatif ("il y a 2j")
