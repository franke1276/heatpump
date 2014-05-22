BEGIN{
  OFMT = "%.01f"
  wp_kwh=0.2251
  sz_kwh=0.2848
}
{
  wp_jahr[$1] += $7
  wp_monat[$1$2] += $7
  sz_jahr[$1] += $8
  sz_monat[$1$2] += $8
} 
END {
  for (j in wp_jahr) {
    for (m in wp_monat) {
      printf   "%d: %.01f(%.02f) %.01f(%.02f)\n", m, wp_monat[m]/10000, (wp_monat[m]/10000*wp_kwh), sz_monat[m]/10000, (sz_monat[m]/10000*sz_kwh)
    }
    printf  "%6d: %.01f(%.02f) %.01f(%.02f)", j, wp_jahr[j]/10000,(wp_jahr[j]/10000*wp_kwh) ,sz_jahr[j]/10000, (sz_jahr[j]/10000*sz_kwh)
    }
}
