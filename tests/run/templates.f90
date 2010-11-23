subroutine gfoo(n, b)
  integer, intent(in) :: n
  double precision, intent(inout), dimension(n) :: b
end subroutine gfoo

subroutine sfoo(n, b)
  integer, intent(in) :: n
  real, intent(inout), dimension(n) :: b
  b = b * 1
end subroutine sfoo

subroutine dfoo(n, b)
  integer, intent(in) :: n
  double precision, intent(inout), dimension(n) :: b
  b = b * 2
end subroutine dfoo

subroutine other(n, b)
  integer, intent(in) :: n
  double precision, intent(inout), dimension(n) :: b
end subroutine other

subroutine cfoo(n, b)
  integer, intent(in) :: n
  complex, intent(inout), dimension(n) :: b
  b = b * 3
end subroutine cfoo

subroutine zfoo(n, b)
  integer, intent(in) :: n
  double complex, intent(inout), dimension(n) :: b
  b = b * 4
end subroutine zfoo

