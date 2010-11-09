
        subroutine testone(m_hidden, m, n, arr)
            ! Assert that m_hidden == m + 1.
            ! Then do arr = arange(m*n).reshape(m, n)
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
        end subroutine testone

