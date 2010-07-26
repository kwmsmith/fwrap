

      subroutine kind_params(a, b, c)
        implicit none
        integer, parameter :: int_ktp = kind(0), real_ktp = kind(0.0)
        integer, parameter :: dbl_ktp = kind(0.0D0)
        integer(kind=int_ktp), intent(inout) :: a
        real(kind=real_ktp), intent(inout) :: b
        real(kind=dbl_ktp), intent(inout) :: c

        a = int(a + b + c + 1, kind=int_ktp)
        b = a + 1.0
        c = b + 1.0D0

      end subroutine
