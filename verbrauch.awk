BEGIN {
  print "["
}{
  print "{" "stunde=" $5 ", wp=" $7+0 " ,sz=" $8+0 "}," 
}END{
  print "]"
}
