subroutine explicit_shape(m, by, arr)
  implicit none
  integer, intent(in) :: m, by
  integer :: idx, i, j
  real*8, dimension(m, by), intent(out) :: arr
  idx = 0
  do i = 1, m
     do j = 1, by
        arr(i, j) = idx
        idx = idx + 1
     end do
  end do
end subroutine explicit_shape

subroutine assumed_shape(m, by, arr)
  implicit none
  integer, intent(in) :: m, by
  integer :: idx, i, j
  real*8, dimension(m, by), intent(out) :: arr
  idx = 0
  do i = 1, m
     do j = 1, by
        arr(i, j) = idx
        idx = idx + 1
     end do
  end do
end subroutine assumed_shape

subroutine noop(n, arr)
  implicit none
  integer, intent(in) :: n
  real*8, dimension(n), intent(out) :: arr
end subroutine

