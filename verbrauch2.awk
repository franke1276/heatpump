BEGIN{
  OFMT = "%.01f"
}
{
  wp[$1$2$3] += $7
} 
END {
    for (t in wp) {
      printf "%d;%.01f\n", t, wp[t]/10000
    }
}
