"""Tests du moteur PNJ, repris de features/pnj/lib/engine.test.ts du site (mêmes données, mêmes attentes)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pnj_data
from pnj_engine import (Zaap, apply_correction, command, convoi_macro_steps, convoi_steps, nearest_zaap, norm, parse_coords, popular, search,
                        zaap_for, zone_hue)

D = pnj_data.load_pnj()


@unittest.skipIf(D is None, "pnj.json introuvable (ni cache, ni copie locale du site)")
class MoteurPnj(unittest.TestCase):
    def test_coordonnees_reconnues(self):
        self.assertEqual(parse_coords("4,-18"), (4, -18))
        self.assertEqual(parse_coords("[-55, 15]"), (-55, 15))
        self.assertIsNone(parse_coords("kerub"))

    def test_accents_et_casse_ignores(self):
        self.assertEqual(norm("  Brâkmar "), "brakmar")

    def test_zaap_le_plus_proche(self):
        self.assertEqual(nearest_zaap(3, -17, D.zaaps), Zaap(5, -18, 95))

    def test_trajet_anti_lag_puis_travel(self):
        r = search("3,-17", D, 0)[0]
        self.assertEqual(command(r, "route", True), "/zaap 5,-18;/zaap 5,-18;/travel 3,-17")
        self.assertEqual(command(r, "route", False), "/zaap 5,-18;/travel 3,-17")
        self.assertEqual(command(r, "pos"), "[3,-17]")
        self.assertEqual(command(r, "travel"), "/travel 3,-17")
        self.assertEqual(command(r, "zaap"), "/zaap 5,-18")

    def test_recherche_pnj_sans_accents_et_zaap_par_zone(self):
        self.assertEqual(search("farle ingals", D, 0)[0].kind, "pnj")
        res = search("zaap astrub", D, 0)
        self.assertTrue(res and all(r.kind == "zaap" for r in res))

    def test_un_zaap_na_pas_de_zaap_conseille(self):
        z = search("5,-18", D, 0)[0]
        self.assertEqual(z.kind, "zaap")
        self.assertEqual(command(z, "route"), "/zaap 5,-18")

    def test_position_et_quete_gardees_et_populaires_localises(self):
        k = search("kartier tremai", D, 0)[0]
        self.assertEqual((k.x, k.y), (10, -1))
        self.assertTrue(k.quest)
        top = popular(D, 0)
        self.assertEqual(len(top), 12)
        self.assertTrue(all(r.quest for r in top))

    def test_zaap_de_la_meme_zone_prioritaire(self):
        z = D.zaaps[0]
        self.assertEqual(zaap_for(999, 999, z.sa, D.zaaps), z)

    def test_teinte_de_zone_stable(self):
        self.assertEqual(zone_hue("Astrub"), zone_hue("Astrub"))
        self.assertTrue(0 <= zone_hue("Cité d'Astrub") < 360)

    def test_correction_locale(self):
        r = search("kartier tremai", D, 0)[0]
        c = apply_correction(r, {"x": 1, "y": 2}, D.zaaps)
        self.assertEqual((c.x, c.y), (1, 2))
        self.assertEqual(apply_correction(r, None, D.zaaps), r)
        c2 = apply_correction(r, {"zaap": [5, -18]}, D.zaaps)
        self.assertEqual((c2.zaap.x, c2.zaap.y), (5, -18))

    def test_convoi_suiveurs_d_abord_chef_en_dernier(self):
        r = search("3,-17", D, 0)[0]
        steps = convoi_steps(r, ["Chef", "A", "B"], "Chef")
        self.assertEqual([s["who"] for s in steps if s["label"] == "zaap"], ["A", "B", "Chef"])
        self.assertEqual([s["label"] for s in steps], ["zaap"] * 3 + ["suivi"] + ["travel"] * 3)
        self.assertEqual(steps[0]["text"], "/zaap 5,-18")
        self.assertEqual(steps[-1]["text"], "/travel 3,-17")
        self.assertEqual(steps[-1]["who"], "Chef")

    def test_convoi_destination_zaap_sans_travel(self):
        z = search("5,-18", D, 0)[0]
        steps = convoi_steps(z, ["A", "Chef"], "Chef")
        self.assertEqual([s["text"] for s in steps], ["/zaap 5,-18"] * 2)

    def test_macro_convoi_ordre_et_syntaxes(self):
        r = search("3,-17", D, 0)[0]
        st = convoi_macro_steps(r, ["A", "B"], "Chef", {"arrival_delay": 5})
        seq = [(s["do"], s.get("who"), s.get("text") or s.get("key")) for s in st if s["do"] != "wait"]
        self.assertEqual(seq, [("paste", "A", "/zaap 5 -18"), ("paste", "B", "/zaap 5 -18"), ("paste", "Chef", "/zaap 5 -18"),
                               ("key", "Chef", "ctrl+w"), ("paste", "Chef", "/travel 3,-17")])
        self.assertEqual([s["s"] for s in st if s.get("label") == "arrivée au zaap"], [5])

    def test_macro_convoi_travel_pour_tous_et_destination_zaap(self):
        r = search("3,-17", D, 0)[0]
        st = convoi_macro_steps(r, ["A"], "Chef", {"travel_all": True})
        self.assertEqual([s["who"] for s in st if s["do"] == "paste" and s["text"].startswith("/travel")], ["Chef", "A"])
        z = search("5,-18", D, 0)[0]
        st = convoi_macro_steps(z, ["A"], "Chef")
        self.assertTrue(all(s["do"] != "key" and not s.get("text", "").startswith("/travel") for s in st))


if __name__ == "__main__":
    unittest.main()
