# images/

Όλες οι θέσεις φωτογραφιών είναι πλέον καλυμμένες — δεν υπάρχει placeholder.

## ⚠ Μην σβήσεις

`marmelanna-wordmark.png` (802×241) — το λογότυπο, αποσπασμένο από την ετικέτα
`Krystallia` με alpha channel. Χρησιμοποιείται σε header, hero και footer.
Αν χρειαστεί ξανά, η πηγή είναι στο `../../etiketes/`.

## Κανόνας ονομάτων

> **Ποτέ ίδιο όνομα αρχείου με διαφορετικό περιεχόμενο.**

Τα `/images/*` έχουν cache μιας ημέρας. Αν αντικαταστήσεις φωτογραφία
κρατώντας το όνομα, όσοι έχουν ήδη επισκεφθεί τη σελίδα βλέπουν την παλιά.
Γι' αυτό τα ονόματα περιγράφουν το **περιεχόμενο**, όχι τη θέση.

## Έτοιμα

Από τις λήψεις στο `../../Frouta Photos/`, με Pillow: crop στο ratio της θέσης,
ήπιο ζέσταμα ώστε να δέσουν με το κρεμ, +10-14% αντίθεση, unsharp mask όπου
βοηθά. Όλες εκτός από το hero έχουν **βάθος πεδίου**: το θέμα μένει καθαρό και
το φόντο θολώνει σε δύο στρώσεις (μισό και πλήρες θόλωμα) με ακτινική μάσκα,
συν διακριτικό vignette. Το script είναι στο ιστορικό του git.
**Στις λήψεις με πυκνό φύλλωμα το sharpening παραλείπεται** — προσθέτει
~12% bytes και θόρυβο χωρίς οπτικό κέρδος.

| Αρχείο | Πηγή | Σημείωση |
|---|---|---|
| `orchard-800.jpg` / `orchard-1300.jpg` | esperidoeidi | hero, με `srcset` |
| `step-1-branch.jpg` | damaskina2 | «Το φρούτο» |
| `step-2-picking.jpg` | sugkomidi2 | «Η συγκομιδή» — κομμένο πάνω από το κάγκελο |
| `step-3-washed.jpg` | damaskina4 | «Η μικρή παραγωγή» |
| `season-spring-lemon.jpg` | λεμονι τελικο | Άνοιξη |
| `season-summer-pears.jpg` | κρυσταλλια δεντρο | Καλοκαίρι |
| `season-winter-persimmons.jpg` | lotoi | Χειμώνας — **πηγή μόλις 387×516** |
| `step-4-jar.jpg` | vazo.heic | «Το βάζο» (μετατροπή HEIC με `sips`) |
| `season-autumn-branch.jpg` | damaskina3 | Φθινόπωρο |

> Το hero έχει **δύο εκδόσεις**. Ο οπωρώνας είναι πολύ πυκνός σε λεπτομέρεια
> και δεν συμπιέζεται (508 KB στα 1500px). Με `srcset` το κινητό κατεβάζει
> 163 KB αντί για 381 KB — και το κινητό είναι η περίπτωση του QR.
> Αν αλλάξει η φωτογραφία, χρειάζονται **και οι δύο** εκδόσεις.

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
