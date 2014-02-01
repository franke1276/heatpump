{
  w[int($5)]+=$7
  s[int($6)]+=$8
  wp=wp + $7
  sz = sz + $8
}
END{
  print "WP: "
  for (i=0;i<=23;i++) 
    print i ": " w[i]/10000 " " s[i]/10000
  print "Summe: " wp/10000 " " sz/10000
}
