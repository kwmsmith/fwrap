
      subroutine testone(m_hidden, m, n, arr)
C     Assert that m_hidden == m + 1.
C     Then do arr = arange(m*n).reshape(m, n)
      integer :: m_hidden, m, n, i, j, idx
      real*8 :: arr(1:m_hidden, 1:n)
      if (m_hidden /= m + 1) then
         write (*,*) 'assumption failed in pyf_support.f'
         arr = 0
      else
         idx = 0
         do i = 1, m_hidden
            do j = 1, n
               arr(i, j) = idx
               idx = idx + 1
            end do
         end do
      end if
      end subroutine
      
      subroutine reorders(x, y, z)
      integer x, z, i
      integer y(4)
      x = 1
      do i = 1, 4
         y(i) = 2
      enddo
      z = 3
      end subroutine

      function fort_sum_simple(n, arr)
      integer i, n
      real*8 fort_sum_simple
      real*8 arr(n)
      fort_sum_simple = 0
      do i = 1, n
         fort_sum_simple = fort_sum_simple + arr(i)
      enddo
      end function

      function fort_sum(n, arr)
      integer i, n
      real*8 fort_sum
      real*8 arr(n)
      fort_sum = 0
      do i = 1, n
         fort_sum = fort_sum + arr(i)
      enddo
      end function
