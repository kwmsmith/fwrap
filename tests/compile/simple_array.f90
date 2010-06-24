      subroutine assumed_size(arr, d1)
        implicit none
        integer, intent(in) :: d1
        complex*16, intent(inout) :: arr(d1, *)

        arr(1:d1, 1) = cmplx(10,20,kind=kind(arr))
      end subroutine assumed_size
      subroutine explicit_shape(arr, d1, d2)
        implicit none
        integer, intent(in) :: d1, d2
        real(kind=8), intent(inout) :: arr(d1,d2)

        arr = 10.0

      end subroutine explicit_shape

      subroutine pass_array(arr0, arr1, arr2)
      implicit none
      integer, dimension(:,:), intent(in) :: arr0
      integer, dimension(:,:), intent(inout) :: arr1
      integer, dimension(:,:), intent(out) :: arr2

      print *, arr0
      print *, arr1

      arr2 = arr1 + arr0

      end subroutine pass_array

      subroutine pass_5D(arr0, arr1, arr2)
      implicit none
      integer :: i,j,k,l,m
      integer, dimension(:,:,:,:,:), intent(in) :: arr0
      integer, dimension(:,:,:,:,:), intent(inout) :: arr1
      integer, dimension(:,:,:,:,:), intent(out) :: arr2

      print *, shape(arr0)
      print *, shape(arr1)
      print *, shape(arr2)
      ! print *, arr0
      ! print *, arr1

      do i = 1, size(arr0,1)
          do j = 1, size(arr0,2)
              do k = 1, size(arr0,3)
                  do l = 1, size(arr0,4)
                      do m = 1, size(arr0,5)
                          print *, arr0(m,l,k,j,i)
                      enddo
                  enddo
              enddo
          enddo
      enddo

      arr2 = arr1 + arr0

      end subroutine pass_5D

      subroutine pass_3D(arr0, arr1, arr2)
      implicit none
      integer :: i,j,k,l,m
      integer, dimension(:,:,:), intent(in) :: arr0
      integer, dimension(:,:,:), intent(inout) :: arr1
      integer, dimension(:,:,:), intent(out) :: arr2

      print *, shape(arr0)
      print *, shape(arr1)
      print *, shape(arr2)
      ! print *, arr0
      ! print *, arr1

      do k = 1, size(arr0,1)
          do l = 1, size(arr0,2)
              do m = 1, size(arr0,3)
                  print *, arr0(m,l,k)
              enddo
          enddo
      enddo

      arr2 = arr1 + arr0

      end subroutine pass_3D

      subroutine pass_2D(arr0, arr1, arr2)
      implicit none
      integer :: i,j,k,l,m
      integer, dimension(:,:,:), intent(in) :: arr0
      integer, dimension(:,:,:), intent(inout) :: arr1
      integer, dimension(:,:,:), intent(out) :: arr2

      print *, shape(arr0)
      print *, shape(arr1)
      print *, shape(arr2)
      ! print *, arr0
      ! print *, arr1

      do l = 1, size(arr0,1)
          do m = 1, size(arr0,2)
              print *, arr0(m,l,1)
          enddo
      enddo

      arr2 = arr1 + arr0

      end subroutine pass_2D
