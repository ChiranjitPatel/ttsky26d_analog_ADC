"""Simple transistor-level drawings of each stage (bias_gen, ota, bandgap_core, ...) for reading the circuits.

Not the source of truth (that is xschem/*.sch). Regenerate: python3 draw_stages.py .
Needs: pip install schemdraw
"""
import sys
import schemdraw
import schemdraw.elements as elm

OUT = sys.argv[1]
schemdraw.config(fontsize=10, lw=1.2)
NETC = "#1565c0"   # net label colour
DEVC = "#555555"   # device annotation colour


class Sch:
    def __init__(self):
        self.d = schemdraw.Drawing(show=False)

    def fet(self, kind, x, ysrc, gate="right", name="", info=""):
        """Place an NFet/PFet by its source. NFet: drain above source; PFet: drain below source."""
        e = (elm.NFet() if kind == "n" else elm.PFet()).right()
        e = e.at((x, ysrc)).anchor("source")
        if gate == "left":
            e = e.reverse()
        e = self.d.add(e)
        a = {k: tuple(e.absanchors[k]) for k in ("drain", "gate", "source")}
        # annotation on the side opposite the gate
        tx = x + (0.25 if gate == "left" else -0.25)
        ha = "left" if gate == "left" else "right"
        ymid = (a["drain"][1] + a["source"][1]) / 2
        self.d.add(elm.Label().at((tx, ymid + 0.3)).label(name, halign=ha, fontsize=10))
        self.d.add(elm.Label().at((tx, ymid - 0.25)).label(info, halign=ha, fontsize=8, color=DEVC))
        return a

    def w(self, *pts, dot_end=False, dot_start=False):
        for p, q in zip(pts, pts[1:]):
            self.d.add(elm.Line().at(p).to(q))
        if dot_start: self.d.add(elm.Dot().at(pts[0]))
        if dot_end: self.d.add(elm.Dot().at(pts[-1]))

    def dot(self, p): self.d.add(elm.Dot().at(p))

    def net(self, p, name, side="right", dy=0.0):
        ha = {"right": "left", "left": "right", "above": "center", "below": "center"}[side]
        off = {"right": (0.15, dy), "left": (-0.15, dy), "above": (0, 0.3), "below": (0, -0.35)}[side]
        self.d.add(elm.Label().at((p[0] + off[0], p[1] + off[1])).label(name, halign=ha, color=NETC, fontsize=10))

    def rail(self, y, x0, x1, name):
        self.w((x0, y), (x1, y))
        self.d.add(elm.Label().at((x0 - 0.2, y)).label(name, halign="right", fontsize=11))

    def gnd(self, p):
        self.d.add(elm.Ground().at(p))

    def title(self, x, y, t, sub=""):
        self.d.add(elm.Label().at((x, y)).label(t, halign="left", fontsize=14))
        if sub: self.d.add(elm.Label().at((x, y - 0.55)).label(sub, halign="left", fontsize=9, color=DEVC))

    def save(self, path):
        self.d.save(path, dpi=130)


# =================================================================== stage 1: bias_gen
s = Sch()
VDD, GND = 11.0, 0.0
s.title(0, 13.2, "Stage 1 — bias_gen (β-multiplier, 1 µA)",
        "all L in µm; W/L shown as W/L ×mult; body of NMOS = VGND, PMOS = VDPWR")
s.rail(VDD, 0, 26, "VDPWR")
s.rail(GND, 0, 26, "VGND")

# PMOS mirror
mp1 = s.fet("p", 2, VDD, "right", "MP1", "pfet_lvt 2/2")
mp2 = s.fet("p", 6, VDD, "left", "MP2", "pfet_lvt 2/2")
s.w(mp1["gate"], mp2["gate"])
pb = (4.0, mp1["gate"][1])
s.dot(pb)
s.w(pb, (4.0, 8.3), (6, 8.3)); s.dot((6, 8.3))          # MP2 diode
s.net((4.0, mp1["gate"][1] + 0.05), "pbias", "above")
# NMOS pair
mn1 = s.fet("n", 2, 3.0, "right", "MN1", "nfet 2/2")
mn2 = s.fet("n", 6, 3.0, "left", "MN2", "nfet 2/2 ×4")
s.w(mn1["gate"], mn2["gate"])
nb = (3.37, 5.2)
s.w(mn1["gate"], (mn1["gate"][0], 5.2), (2, 5.2)); s.dot((2, 5.2)); s.dot(mn1["gate"])   # MN1 diode
s.net((2, 6.6), "nbias", "left")
s.w(mp1["drain"], mn1["drain"])
s.w(mp2["drain"], mn2["drain"])
s.w(mn1["source"], (2, GND)); s.dot((2, GND))
r1 = s.d.add(elm.Resistor().down().at(mn2["source"]).to((6, GND)).label("R1\n≈63 kΩ\nxhigh 0.35/11", loc="bottom", fontsize=8))
s.dot((6, GND))
s.net((6, 2.6), "nr", "right")
s.dot((2, VDD)); s.dot((6, VDD))

# startup
s.d.add(elm.Label().at((9.2, 12.0)).label("startup", halign="left", fontsize=11, color=DEVC))
mpd2 = s.fet("p", 12, VDD, "right", "MPD2", "pfet 0.42/0.15")
s.net(mpd2["gate"], "pd", "right")
ms2 = s.fet("p", 12, mpd2["drain"][1] - 0.4, "right", "MS2", "pfet 0.42/50")
s.w(mpd2["drain"], ms2["source"])
s.w(ms2["gate"], (ms2["gate"][0] + 0.5, ms2["gate"][1]), (ms2["gate"][0] + 0.5, ms2["gate"][1] - 0.4)); s.gnd((ms2["gate"][0] + 0.5, ms2["gate"][1] - 0.4))
ms3 = s.fet("n", 12, 2.2, "left", "MS3", "nfet 2/2")
s.w(ms2["drain"], ms3["drain"])
s.net((12, (ms2["drain"][1] + ms3["drain"][1]) / 2 + 0.55), "su", "right")
s.w(ms3["source"], (12, GND)); s.dot((12, GND))
s.net(ms3["gate"], "nbias", "left")
ms1 = s.fet("n", 9.0, 5.0, "right", "MS1", "nfet 0.42/1")
s.w(ms1["drain"], (9.0, 8.3), (6, 8.3))
su_y = ms1["gate"][1]
s.w(ms1["gate"], (12, su_y)); s.dot((12, su_y))
s.w(ms1["source"], (9.0, GND)); s.dot((9.0, GND))
s.dot((12, VDD))

# power-down switches (connected by net name)
s.d.add(elm.Label().at((15.0, 12.0)).label("power-down (pd = 1 → off)", halign="left", fontsize=11, color=DEVC))
mpd1 = s.fet("p", 16, VDD, "right", "MPD1", "pfet 0.42/0.15")
s.net(mpd1["gate"], "pdb", "right"); s.net(mpd1["drain"], "pbias", "below"); s.dot((16, VDD))
mnd1 = s.fet("n", 16, 2.0, "right", "MND1", "nfet 0.42/0.15")
s.net(mnd1["gate"], "pd", "right"); s.net(mnd1["drain"], "nbias", "above"); s.w(mnd1["source"], (16, GND)); s.dot((16, GND))
mnd2 = s.fet("n", 20, 2.0, "right", "MND2", "nfet 0.42/0.15")
s.net(mnd2["gate"], "pd", "right"); s.net(mnd2["drain"], "su", "above"); s.w(mnd2["source"], (20, GND)); s.dot((20, GND))
# inverter pd -> pdb
mip = s.fet("p", 24, VDD, "left", "MIP", "pfet 0.84/0.15")
mn_ = s.fet("n", 24, 4.0, "left", "MIN", "nfet 0.42/0.15")
s.w(mip["drain"], mn_["drain"]); s.w(mn_["source"], (24, GND)); s.dot((24, GND)); s.dot((24, VDD))
gx = mip["gate"][0] - 0.6
s.w(mip["gate"], (gx, mip["gate"][1]), (gx, mn_["gate"][1]), mn_["gate"])
s.dot((gx, (mip["gate"][1] + mn_["gate"][1]) / 2)); s.net((gx, (mip["gate"][1] + mn_["gate"][1]) / 2), "pd", "left")
s.dot((24, 7.0)); s.w((24, 7.0), (25.2, 7.0)); s.net((25.2, 7.0), "pdb", "right")

# ports
s.d.add(elm.Label().at((0, -1.4)).label("Ports: VDPWR, VGND, pd (in), nbias (out), pbias (out).   "
        "nbias → gate of nfet 2/2 sinks 1 µA;  pbias → gate of pfet_lvt 2/2 sources 1 µA.", halign="left", fontsize=9))
s.save(f"{OUT}/stage1_bias_gen.png")

# =================================================================== stage 2: ota
s = Sch()
VDD, GND = 11.0, 0.0
s.title(0, 13.2, "Stage 2 — ota (two-stage Miller, PMOS input)",
        "all L in µm; W/L shown as W/L ×mult; body of NMOS = VGND, PMOS = VDPWR; pbias from bias_gen")
s.rail(VDD, 0, 22, "VDPWR")
s.rail(GND, 0, 22, "VGND")

m5 = s.fet("p", 4, VDD, "right", "M5", "pfet_lvt 2/2 ×2  (2 µA)")
s.net(m5["gate"], "pbias", "right"); s.dot((4, VDD))
TY = 8.6
s.w(m5["drain"], (4, TY)); s.w((2, TY), (6, TY)); s.dot((4, TY)); s.net((4, TY), "tail", "below")
m1 = s.fet("p", 2, TY, "left", "M1", "pfet_lvt 8/2")
m2 = s.fet("p", 6, TY, "right", "M2", "pfet_lvt 8/2")
s.net(m1["gate"], "inn  (−)", "left"); s.net(m2["gate"], "inp  (+)", "right")
m3 = s.fet("n", 2, 1.5, "right", "M3", "nfet 1/4")
m4 = s.fet("n", 6, 1.5, "left", "M4", "nfet 1/4")
s.w(m3["gate"], m4["gate"]); s.dot(m3["gate"])
s.w(m3["gate"], (m3["gate"][0], 4.2), (2, 4.2)); s.dot((2, 4.2))      # M3 diode
s.w(m1["drain"], m3["drain"]); s.w(m2["drain"], m4["drain"])
s.net((2, 5.6), "d1", "left")
s.w(m3["source"], (2, GND)); s.w(m4["source"], (6, GND)); s.dot((2, GND)); s.dot((6, GND))
# out1 -> M6 gate
O1 = (6, 4.6)
s.dot(O1); s.net((6, 5.25), "out1", "left")
m6 = s.fet("n", 11, 1.5, "left", "M6", "nfet 1/4 ×4  (4 µA)")
s.w(O1, (9.0, 4.6), (9.0, m6["gate"][1]), m6["gate"])
s.w(m6["source"], (11, GND)); s.dot((11, GND))
m7 = s.fet("p", 11, VDD, "right", "M7", "pfet_lvt 2/2 ×4  (4 µA)")
s.net(m7["gate"], "pbias", "right"); s.dot((11, VDD))
s.w(m7["drain"], m6["drain"])
# Miller compensation out1 -- RZ -- CC -- out
CY = 6.6
s.dot((6, CY))
s.d.add(elm.Resistor().right().at((6, CY)).to((8.4, CY)).label("RZ ≈40 kΩ", loc="top", fontsize=8))
s.d.add(elm.Capacitor().right().at((8.4, CY)).to((11, CY)).label("CC 0.7 pF\nMIM", loc="top", fontsize=8))
s.dot((11, CY)); s.net((8.4, CY), "cz", "below")
# output
OY = 5.2
s.dot((11, OY)); s.w((11, OY), (16.5, OY)); s.d.add(elm.Dot(open=True).at((16.5, OY)))
s.net((16.5, OY), "out", "right")
# power-down
s.d.add(elm.Label().at((13.2, 12.0)).label("power-down (pd = 1 → off)", halign="left", fontsize=11, color=DEVC))
mpd = s.fet("p", 15, VDD, "right", "MPD", "pfet 0.42/0.15")
s.net(mpd["gate"], "pdb", "right"); s.dot((15, VDD))
s.w(mpd["drain"], (15, OY)); s.dot((15, OY))
mnd = s.fet("n", 18, 1.5, "right", "MND", "nfet 0.42/0.15")
s.net(mnd["gate"], "pd", "right"); s.net(mnd["drain"], "out1", "above"); s.w(mnd["source"], (18, GND)); s.dot((18, GND))
s.d.add(elm.Label().at((18.6, 8.2)).label("+ local inverter pd → pdb\n  (MIP pfet 0.84/0.15, MIN nfet 0.42/0.15),\n  same as in bias_gen", halign="left", fontsize=8, color=DEVC))
s.d.add(elm.Label().at((0, -1.4)).label("Ports: VDPWR, VGND, pbias (in), pd (in), inp (in), inn (in), out (out).   "
        "Stage 1: M1/M2 pair + M3/M4 mirror → out1.  Stage 2: M6 common source + M7 load → out.", halign="left", fontsize=9))
s.save(f"{OUT}/stage2_ota.png")

# =================================================================== stage 3: bandgap_core
s = Sch()
VDD, GND = 13.0, 0.0
s.title(0, 15.2, "Stage 3 — bandgap_core (VBG = Vbe + (R2/R1)·ΔVbe ≈ 1.215 V)",
        "all L in µm; W/L shown as W/L ×mult; body of NMOS = VGND, PMOS = VDPWR; R units = res_xhigh_po 0.35/2 ≈ 12.1 kΩ")
s.rail(VDD, 0, 28.5, "VDPWR")
s.rail(GND, 0, 28.5, "VGND")

def pnp(x, ytop, name, info):
    q = s.d.add(elm.BjtPnp(circle=True).right().at((x, ytop)).anchor("emitter"))
    b, c = tuple(q.absanchors["base"]), tuple(q.absanchors["collector"])
    s.w(c, (x, GND)); s.dot((x, GND))
    s.w(b, (b[0] - 0.5, b[1]), (b[0] - 0.5, GND)); s.dot((b[0] - 0.5, GND))
    s.d.add(elm.Label().at((x + 0.5, ytop - 0.4)).label(name, halign="left", fontsize=10))
    s.d.add(elm.Label().at((x + 0.5, ytop - 0.95)).label(info, halign="left", fontsize=8, color=DEVC))

mpa = s.fet("p", 3, VDD, "left", "MPA", "pfet 8/4")
mpb = s.fet("p", 7.5, VDD, "left", "MPB", "pfet 8/4")
mpc = s.fet("p", 12, VDD, "left", "MPC", "pfet 8/4")
for m in (mpa, mpb, mpc):
    s.net(m["gate"], "vgp", "left")
for x in (3, 7.5, 12):
    s.dot((x, VDD))
# branch A: Q1
s.w(mpa["drain"], (3, 4.5)); s.dot((3, 8.5)); s.net((3, 8.5), "va", "right")
pnp(3, 4.5, "Q1", "PNP ×1")
# branch B: R1 + Q2
s.w(mpb["drain"], (7.5, 9.5)); s.dot((7.5, 10.2)); s.net((7.5, 10.2), "vb", "right")
s.d.add(elm.Resistor().down().at((7.5, 9.5)).to((7.5, 6.5)).label("R1 = 2 units\n≈ 24 kΩ", loc="bottom", fontsize=8))
s.w((7.5, 6.5), (7.5, 4.5)); s.net((7.5, 5.6), "vq2", "right")
pnp(7.5, 4.5, "Q2", "PNP ×8")
# branch C: R2 + Q3 and output
s.w(mpc["drain"], (12, 9.5)); s.dot((12, 10.2))
s.d.add(elm.Resistor().down().at((12, 9.5)).to((12, 6.5)).label("R2 = 19 units\n≈ 230 kΩ", loc="bottom", fontsize=8))
s.w((12, 6.5), (12, 4.5)); s.net((12, 5.6), "vq3", "right")
pnp(12, 4.5, "Q3", "PNP ×1")
s.w((12, 10.2), (16, 10.2)); s.d.add(elm.Dot(open=True).at((16, 10.2))); s.net((16, 10.2), "vbg", "right")
# OTA
o = s.d.add(elm.Opamp(leads=True).right().at((20.0, 6.0)).anchor("out"))
i1, i2, oo = tuple(o.absanchors["in1"]), tuple(o.absanchors["in2"]), tuple(o.absanchors["out"])
s.net(i1, "va  (inn)", "left"); s.net(i2, "vb  (inp)", "left"); s.net(oo, "vgp", "right")
s.d.add(elm.Label().at((16.8, 4.3)).label("ota (stage 2)\npbias, pd", halign="left", fontsize=8, color=DEVC))
s.d.add(elm.Label().at((14.2, 8.0)).label("OTA forces va = vb\n→ I = ΔVbe / R1 ≈ 2.26 µA per branch", halign="left", fontsize=9, color=DEVC))
# startup
s.d.add(elm.Label().at((22.0, 14.0)).label("startup", halign="left", fontsize=11, color=DEVC))
msu2 = s.fet("p", 24, VDD, "left", "MSU2", "pfet_lvt 2/2 (1 µA)")
s.net(msu2["gate"], "pbias", "left"); s.dot((24, VDD))
msu3 = s.fet("n", 24, 4.0, "left", "MSU3", "nfet 1/1")
s.w(msu2["drain"], msu3["drain"]); s.net(msu3["gate"], "vbg", "left")
s.w(msu3["source"], (24, GND)); s.dot((24, GND))
SU = (24, 8.0); s.dot(SU); s.net(SU, "su", "right")
msu1 = s.fet("n", 27.6, 4.0, "left", "MSU1", "nfet 0.42/1")
s.w(SU, (25.8, 8.0), (25.8, msu1["gate"][1]), msu1["gate"])
s.net(msu1["drain"], "vgp", "above"); s.w(msu1["source"], (27.6, GND)); s.dot((27.6, GND))
msd = s.fet("n", 21.0, 1.0, "left", "MSD", "nfet 0.42/0.15")
s.net(msd["drain"], "su", "above"); s.net(msd["gate"], "pd", "left"); s.w(msd["source"], (21.0, GND)); s.dot((21.0, GND))
s.d.add(elm.Label().at((0, -1.4)).label("Ports: VDPWR, VGND, pbias (in), pd (in), vbg (out), vgp (out, for the PTAT branch).   "
        "Startup: while vbg is low, MSU2 pulls su high and MSU1 pulls vgp low; once vbg is up, MSU3 holds su low.", halign="left", fontsize=9))
s.save(f"{OUT}/stage3_bandgap_core.png")

# =================================================================== stage 4: ptat_out
s = Sch()
VDD, GND = 9.0, 0.0
s.title(0, 11.2, "Stage 4 — ptat_out (VPTAT = ΔVbe · R3/R1 ≈ 0.60 V, 2.0 mV/°C)",
        "MPP copies the bandgap branch current I = ΔVbe/R1; R3 uses the same xhigh_po 0.35/2 unit as R1, so the resistor TC cancels")
s.rail(VDD, 0, 12, "VDPWR")
s.rail(GND, 0, 12, "VGND")
mpp = s.fet("p", 4, VDD, "left", "MPP", "pfet 8/4  (≈ 2.26 µA)")
s.net(mpp["gate"], "vgp  (from bandgap_core)", "left"); s.dot((4, VDD))
s.w(mpp["drain"], (4, 6.0)); s.dot((4, 6.6))
s.w((4, 6.6), (8, 6.6)); s.d.add(elm.Dot(open=True).at((8, 6.6))); s.net((8, 6.6), "vptat", "right")
s.d.add(elm.Resistor().down().at((4, 6.0)).to((4, 1.5)).label("R3 = 22 units\n≈ 266 kΩ", loc="bottom", fontsize=8))
s.w((4, 1.5), (4, GND)); s.dot((4, GND))
s.d.add(elm.Label().at((0, -1.4)).label("Ports: VDPWR, VGND, vgp (in), vptat (out).   Only a gate touches the core, so loading vptat can't disturb VBG.   "
        "Power-down: vgp = VDPWR → MPP off → vptat = 0 V.", halign="left", fontsize=9))
s.save(f"{OUT}/stage4_ptat_out.png")

# =================================================================== stage 5: vref_filt + vref_buf + vref_sel
import schemdraw.logic as logic
s = Sch()
VDD, GND = 11.0, 0.0
s.title(0, 13.2, "Stage 5 — VREF chain: vref_filt → vref_buf → vref (+ vref_sel to ua[1])",
        "all L in µm; W/L shown as W/L ×mult; body of NMOS = VGND, PMOS = VDPWR")
s.rail(VDD, 0, 30, "VDPWR")
s.rail(GND, 0, 30, "VGND")
# filter
s.d.add(elm.Label().at((0.3, 12.0)).label("vref_filt", halign="left", fontsize=11, color=DEVC))
s.d.add(elm.Dot(open=True).at((0.5, 6.0))); s.net((0.5, 6.0), "vbg", "above")
s.d.add(elm.Resistor().right().at((0.5, 6.0)).to((4.0, 6.0)).label("RF ≈ 1.04 MΩ\n9 × xhigh 0.35/20", loc="top", fontsize=8))
s.dot((4.0, 6.0)); s.net((4.0, 6.0), "vbg_f", "above")
s.d.add(elm.Capacitor().down().at((4.0, 6.0)).to((4.0, GND)).label("CF ≈ 3.9 pF\nnfet gate 10/10 ×5", loc="bottom", fontsize=8))
s.dot((4.0, GND))
# buffer
s.d.add(elm.Label().at((6.5, 12.0)).label("vref_buf (follower, 10 µA)", halign="left", fontsize=11, color=DEVC))
m3 = s.fet("p", 8, VDD, "right", "M3", "pfet_lvt 4/1")
m4 = s.fet("p", 12, VDD, "left", "M4", "pfet_lvt 4/1")
s.w(m3["gate"], m4["gate"]); gx = m3["gate"][0] + 0.4
s.dot((gx, m3["gate"][1])); s.w((gx, m3["gate"][1]), (gx, 8.6), (8, 8.6)); s.dot((8, 8.6))
s.dot((8, VDD)); s.dot((12, VDD)); s.net((8, 8.0), "dm", "left")
TY = 3.2
m1 = s.fet("n", 8, TY, "left", "M1", "nfet 4/1")
m2 = s.fet("n", 12, TY, "right", "M2", "nfet 4/1")
s.w(m3["drain"], m1["drain"]); s.w(m4["drain"], m2["drain"])
s.w((4.0, 6.0), (5.4, 6.0), (5.4, m1["gate"][1]), m1["gate"])
s.w(m1["source"], (8, TY - 0.3), (12, TY - 0.3), m2["source"]); s.dot((10, TY - 0.3)); s.net((10, TY - 0.3), "tail", "below")
msw = s.fet("n", 10, 1.0, "right", "MSW", "nfet 4/0.15")
s.w((10, TY - 0.3), msw["drain"]); s.net(msw["gate"], "en", "right")
s.d.add(elm.Label().at((10.3, 0.35)).label("(MSW source → MT nfet 2/2 ×10, gate nbias, 10 µA → VGND)", halign="left", fontsize=8, color=DEVC))
s.w(msw["source"], (10, GND)); s.dot((10, GND))
VR = (12, 6.6)
s.dot(VR); s.w(m2["gate"], (m2["gate"][0] + 0.6, m2["gate"][1]), (m2["gate"][0] + 0.6, 6.6), VR)
s.w(VR, (16, 6.6)); s.dot((16, 6.6))
s.d.add(elm.Capacitor().down().at((16, 6.6)).to((16, GND)).label("CRES ≈ 5.4 pF\nnfet gate 10/10 ×7", loc="bottom", fontsize=8)); s.dot((16, GND))
s.w((16, 6.6), (18.5, 6.6)); s.d.add(elm.Dot(open=True).at((18.5, 6.6))); s.net((18.5, 6.6), "vref → DAC", "above")
s.d.add(elm.Label().at((12.6, 9.0)).label("MPU pfet 0.42/0.15: pulls dm to VDPWR\nwhen en = 0 → output high-Z", halign="left", fontsize=8, color=DEVC))
# selection
s.d.add(elm.Label().at((20.0, 12.0)).label("vref_sel", halign="left", fontsize=11, color=DEVC))
s.d.add(logic.Nor(inputs=2).at((21.0, 9.6)).anchor("in1").right())
s.d.add(elm.Label().at((20.9, 9.6)).label("ref_sel", halign="right", color=NETC, fontsize=9))
s.d.add(elm.Label().at((20.9, 8.6)).label("bg_pd", halign="right", color=NETC, fontsize=9))
s.d.add(elm.Label().at((24.7, 9.1)).label("en_buf (→ en)", halign="left", color=NETC, fontsize=9))
s.d.add(logic.Or(inputs=2).at((21.0, 5.6)).anchor("in1").right())
s.d.add(elm.Label().at((20.9, 5.6)).label("ref_sel", halign="right", color=NETC, fontsize=9))
s.d.add(elm.Label().at((20.9, 4.6)).label("vref_oe", halign="right", color=NETC, fontsize=9))
s.d.add(elm.Label().at((24.7, 5.1)).label("en_pad", halign="left", color=NETC, fontsize=9))
# TG drawn as a switch
s.d.add(elm.Dot(open=True).at((21.5, 2.4))); s.net((21.5, 2.4), "vref", "left")
s.d.add(elm.Switch().right().at((21.5, 2.4)).to((24.5, 2.4)).label("TG: nfet 10/0.15 + pfet_lvt 20/0.35\non when en_pad = 1", loc="top", fontsize=8))
s.d.add(elm.Dot(open=True).at((24.5, 2.4))); s.net((24.5, 2.4), "pad → ua[1]", "right")
s.d.add(elm.Label().at((0, -1.4)).label("Internal ref (REF_SEL = 0): buffer on, vref ≈ 1.214 V. External ref (REF_SEL = 1): buffer off, ua[1] drives vref through the TG. "
        "DMM readout: REF_SEL = 0, VREF_OE = 1.", halign="left", fontsize=9))
s.save(f"{OUT}/stage5_vref.png")

# =================================================================== stage 7: inmux + vcm_gen
s = Sch()
VDD, GND = 11.0, 0.0
s.title(0, 13.2, "Stage 7 — inmux (4:1 TG mux) and vcm_gen (common mode + top-plate switch)",
        "TG = nfet 4/0.15 + pfet_lvt 8/0.35; decoder: static NOR2/INV on INSEL[1:0] (uio[7:6]) → one-hot en0..en3")
s.rail(VDD, 0, 22, "VDPWR")
s.rail(GND, 0, 22, "VGND")
BUS = 7.0
for k, (name, y) in enumerate((("vin (ua[0])", 8.5), ("vptat", 6.5), ("vbg", 4.5), ("VGND", 2.5))):
    s.d.add(elm.Dot(open=True).at((1.0, y))); s.net((1.0, y), name, "left")
    s.d.add(elm.Switch().right().at((1.0, y)).to((4.0, y)).label(f"en{k}  (INSEL = {k:02b})", loc="top", fontsize=8))
    s.w((4.0, y), (5.0, y), (5.0, 2.5) if k == 3 else (5.0, y)); s.dot((5.0, y))
s.w((5.0, 8.5), (5.0, 2.5)); s.w((5.0, 5.5), (BUS, 5.5)); s.d.add(elm.Dot(open=True).at((BUS, 5.5))); s.net((BUS, 5.5), "vadc → DAC bottom-plate bus", "below")
s.d.add(elm.Dot().at((5.0, 5.5)))
# vcm_gen
mb = s.fet("p", 16, VDD, "right", "MB", "pfet_lvt 2/2 ×10 (10 µA)")
s.net(mb["gate"], "pbias", "right"); s.dot((16, VDD))
md_ = s.fet("n", 16, 1.5, "right", "MD", "nfet 4/1 (diode)")
s.w(mb["drain"], md_["drain"]); s.w(md_["source"], (16, GND)); s.dot((16, GND))
s.w(md_["gate"], (md_["gate"][0], 4.6), (16, 4.6)); s.dot((16, 4.6)); s.dot(md_["gate"])
VC = (16, 6.0); s.dot(VC)
s.w(VC, (19.5, 6.0)); s.dot((19.5, 6.0)); s.net((19.5, 6.6), "vcm ≈ 0.72 V (→ comparator inn)", "right")
s.d.add(elm.Capacitor().down().at((19.5, 6.0)).to((19.5, GND)).label("CV ≈ 2 pF\nnfet gate 8/8 ×4", loc="bottom", fontsize=8)); s.dot((19.5, GND))
s.d.add(elm.Switch().left().at((16, 6.0)).to((12.5, 6.0)).label("MTOP nfet 1/0.15\n(on while smp = 1)", loc="top", fontsize=8))
s.d.add(elm.Dot(open=True).at((12.5, 6.0))); s.net((12.5, 6.0), "vtop (DAC top plate)", "left")
s.d.add(elm.Label().at((0, -1.4)).label("VIN is sampled at 1 MHz (settles in 0.3 µs). VPTAT/VBG have ≈ 250 kΩ source impedance: convert them with clk ≤ 100 kHz (settle in ≈ 4 µs). "
        "vcm cancels: top plate sampled to vcm and compared against the same node.", halign="left", fontsize=9))
s.save(f"{OUT}/stage7_inmux_vcm.png")

# =================================================================== stage 6: comparator
s = Sch()
VDD, GND = 12.0, 0.0
s.title(0, 14.2, "Stage 6 — comparator: PMOS-input StrongARM + inverters + NAND SR latch",
        "all L in µm; reset while clk = 0 (clkb = 1), evaluate while clk = 1; q = 1 when inp > inn")
s.rail(VDD, 0, 24, "VDPWR")
s.rail(GND, 0, 24, "VGND")
mt = s.fet("p", 6, VDD, "right", "MT", "pfet 4/0.15")
s.net(mt["gate"], "clkb", "right"); s.dot((6, VDD))
TS = 10.0
s.w(mt["drain"], (6, TS)); s.w((3, TS), (9, TS)); s.dot((6, TS)); s.net((6, TS), "ts", "below")
m1 = s.fet("p", 3, TS, "left", "M1", "pfet_lvt 4/0.5"); s.net(m1["gate"], "inp", "left")
m2 = s.fet("p", 9, TS, "right", "M2", "pfet_lvt 4/0.5"); s.net(m2["gate"], "inn", "right")
s.net((3, 8.1), "xn", "left"); s.net((9, 8.1), "xp", "right")
m4 = s.fet("p", 3, 7.6, "left", "M4", "pfet 1/0.15")
m3 = s.fet("p", 9, 7.6, "right", "M3", "pfet 1/0.15")
s.w(m1["drain"], m4["source"]); s.w(m2["drain"], m3["source"])
m6 = s.fet("n", 3, 1.5, "left", "M6", "nfet 1/0.15")
m5 = s.fet("n", 9, 1.5, "right", "M5", "nfet 1/0.15")
s.w(m4["drain"], m6["drain"]); s.w(m3["drain"], m5["drain"])
s.w(m6["source"], (3, GND)); s.w(m5["source"], (9, GND)); s.dot((3, GND)); s.dot((9, GND))
ON, OP = (3, 4.6), (9, 4.6)
s.dot(ON); s.dot(OP); s.net((3, 4.6), "on", "left"); s.net((9, 4.6), "op", "right")
# cross coupling: gates of M4/M6 to op, gates of M3/M5 to on
for g, nm, side in ((m4["gate"], "op", "left"), (m6["gate"], "op", "left"), (m3["gate"], "on", "right"), (m5["gate"], "on", "right")):
    s.net(g, nm + "  (cross-coupled)", side)
s.d.add(elm.Label().at((0.2, 12.9)).label("reset nfets 0.42/0.15 (gate clkb) pull xp, xn, op, on to VGND", halign="left", fontsize=8, color=DEVC))
# output stage
s.d.add(logic.Not().at((15.0, 7.0)).anchor("in1").right()); s.net((15.0, 7.0), "op", "left"); s.net((17.6, 7.0), "opb", "above")
s.d.add(logic.Not().at((15.0, 3.0)).anchor("in1").right()); s.net((15.0, 3.0), "on", "left"); s.net((17.6, 3.0), "onb", "below")
s.d.add(logic.Nand(inputs=2).at((19.0, 7.3)).anchor("in1").right()); s.net((19.0, 7.3), "opb", "left"); s.net((19.0, 6.3), "qb", "left"); s.net((22.6, 6.8), "q", "right")
s.d.add(logic.Nand(inputs=2).at((19.0, 3.3)).anchor("in1").right()); s.net((19.0, 3.3), "onb", "left"); s.net((19.0, 2.3), "q", "left"); s.net((22.6, 2.8), "qb", "right")
s.d.add(elm.Label().at((14.5, 9.5)).label("identical inverters keep the latch load on op/on\nequal and independent of the stored state", halign="left", fontsize=8, color=DEVC))
s.d.add(elm.Label().at((0, -1.4)).label("Evaluate: the side with the LOWER input conducts more; its node rises first and the latch regenerates. "
        "op (on the inn side) goes high when inp > inn → q = 1.", halign="left", fontsize=9))
s.save(f"{OUT}/stage6_comparator.png")
print("ok")
