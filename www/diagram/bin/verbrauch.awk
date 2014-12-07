BEGIN{
  OFMT = "%.01f"
  print basis ";2013;2014;2015"
}
{
  if (basis == "monat"){
    ind=$2
  } else {
    ind=$3
  }
  if (zaehler == "wp"){
    counter = $7
  }else {
    counter = $8
  }

  if ($1 == "2013" && ((basis == "monat") || (basis == "tag" && monat == $2))){
    zaehler_2013[ind] += counter
  }
  if ($1 == "2014" && ((basis == "monat") || (basis == "tag" && monat == $2))){
    zaehler_2014[ind] += counter
  }
  if ($1 == "2015" && ((basis == "monat") || (basis == "tag" && monat == $2))){
    zaehler_2015[ind] += counter
  }
} 
END {
  if (basis == "monat"){
    endind=12
  } else {
    endind=31
  }

  for (i = 1; i <= endind; i++){
    m = sprintf("%02d", i)
    printf "%s;%.01f;%.01f;%.01f\n", m, zaehler_2013[m]/10000, zaehler_2014[m]/10000, zaehler_2015[m]/10000
  }
}
