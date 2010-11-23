subroutine s_differ_in_number(x)
  integer :: x
end subroutine

subroutine d_differ_in_number(x, y)
  integer :: x, y
end subroutine

subroutine s_differ_in_dimension(x)
  integer :: x
end subroutine

subroutine d_differ_in_dimension(x)
  integer, dimension(:) :: x
end subroutine


subroutine gfoo(n, b)
  integer, intent(in) :: n
  double precision, intent(inout), dimension(n) :: b
end subroutine

subroutine sfoo(n, b)
  integer, intent(in) :: n
  real, intent(inout), dimension(n) :: b
  b = b * 1
end subroutine

subroutine dfoo(n, b)
  integer, intent(in) :: n
  double precision, intent(inout), dimension(n) :: b
  b = b * 2
end subroutine

subroutine other(n, b)
  integer, intent(in) :: n
  double precision, intent(inout), dimension(n) :: b
end subroutine

subroutine cfoo(n, b)
  integer, intent(in) :: n
  complex, intent(inout), dimension(n) :: b
  b = b * 3
end subroutine

subroutine zfoo(n, b)
  integer, intent(in) :: n
  double complex, intent(inout), dimension(n) :: b
  b = b * 4
end subroutine


