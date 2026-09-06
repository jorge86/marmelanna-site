# images/

Εδώ μπαίνουν οι πραγματικές φωτογραφίες.

## ⚠ Μην σβήσεις

`marmelanna-wordmark.png` (802×241) — το λογότυπο, αποσπασμένο από την ετικέτα
`Krystallia` με alpha channel. Χρησιμοποιείται σε header, hero και footer.
Παράχθηκε με keying του χαρτιού σε διαφάνεια και ισοπέδωση του μελανιού σε δύο
σταθερά χρώματα (λαδί + κοραλί καρδιά), που κρατάει το αρχείο στα 38 KB αντί
για 99 KB. Αν χρειαστεί ξανά, η πηγή είναι στο `../../etiketes/`.

## Τι λείπει

| Αρχείο | Τι δείχνει | Αναλογία | Πού μπαίνει |
|---|---|---|---|
| `orchard.jpg` | Οπωρώνας / καρποί στο δέντρο | 3:2 | index — hero (⚑ PHOTO 01) |
| `step-1-fruit.jpg` | Καρποί πάνω στα δέντρα | 4:3 | index — βήμα 1 (⚑ PHOTO 02) |
| `step-3-cooking.jpg` | Προετοιμασία / βράσιμο | 4:3 | index — βήμα 3 (⚑ PHOTO 04) |
| `step-4-jars.jpg` | Τελικά βάζα | 4:3 | index — βήμα 4 (⚑ PHOTO 05) |

| `season-spring.jpg` | Ανοιξιάτικοι καρποί | 3:2 | epoxes (⚑ PHOTO 08) |
| `season-summer.jpg` | Αχλάδια στο δέντρο | 3:2 | epoxes (⚑ PHOTO 09) |
| `season-winter.jpg` | Λωτοί / κυδώνια | 3:2 | epoxes (⚑ PHOTO 11) |

## Μεγέθη

- Πλάτος 1600 px φτάνει και περισσεύει· πάνω από αυτό απλώς αργεί το QR-scan σε 3G.
- JPEG ποιότητα ~78. Στόχος: κάτω από 250 KB ανά φωτογραφία.
- Το `og-image.jpg` πρέπει να είναι ακριβώς 1200×630 για να μην κόβεται σε Facebook/WhatsApp/Viber.

## Έτοιμα

- `step-2-harvest.jpg` (1200×900) και `season-autumn.jpg` (1400×933) — από τις
  λήψεις δαμάσκηνων στο `../../Frouta Photos/`. Crop στο ratio της θέσης, ήπιο
  ζέσταμα ώστε να δέσουν με το κρεμ, +14% αντίθεση, +12% κορεσμός, unsharp mask.
  Το script είναι στο ιστορικό του git, στο commit που τις πρόσθεσε.

- `label-kontoules.jpg`, `label-krystallia.jpg`, `label-vanilies.jpg` — οι
  πραγματικές ετικέτες, από τα 600 dpi PNG του
  `../../etiketes/telikes gia diastasi 140x70/`, σμικρυμένες σε 1200×600
  (2:1, όπως τα 140×70 mm του πρωτοτύπου):
  ```bash
  sips -Z 1200 -s format jpeg -s formatOptions 78 kontoyles.png --out label-kontoules.jpg
  ```
  Χρησιμοποιούνται ως εικόνες προϊόντος στην αρχική. Αν τυπωθεί νέα ετικέτα,
  ξαναπέρασέ τη από την ίδια εντολή.
- `og-image.jpg` — 1200×630, η ετικέτα Κρυστάλλια με κρεμ γέμισμα:
  ```bash
  sips --padToHeightWidth 630 1200 --padColor F5EEE2 label-krystallia.jpg \
       -s format jpeg -s formatOptions 82 --out og-image.jpg
  ```
- `/favicon.svg` — αχλάδι σε λαδί πάνω σε χαρτί
- `/apple-touch-icon.png` — 180×180, παραγόμενο από το favicon:
  ```bash
  sips -s format png -Z 180 favicon.svg --out apple-touch-icon.png
  ```
