      subroutine explicit_shape(ll, n1, n2, ain, aout, ainout, ano)
        implicit none
        integer, intent(in) :: ll, n1, n2
        character(len=ll), dimension(n1, n2), intent(in) :: ain
        character(len=ll), dimension(n1, n2), intent(out) :: aout
        character(len=ll), dimension(n1, n2), intent(inout) :: ainout
        character(len=ll), dimension(n1, n2) :: ano

        aout = ain
        ano = ainout
        ainout = ain(:,:)(1:ll/2) // ano(:,:)(ll/2+1:ll)
      end subroutine explicit_shape

      subroutine assumed_shape(ain, aout, ainout, ano)
        implicit none
        character(*), dimension(:, :), intent(in) :: ain
        character(*), dimension(:, :), intent(out) :: aout
        character(*), dimension(:, :), intent(inout) :: ainout
        character(*), dimension(:, :) :: ano

        integer ll

        ll = len(ain)

        aout = ain
        ano = ainout
        ainout = ain(:,:)(1:ll/2) // ano(:,:)(ll/2+1:ll)
      end subroutine assumed_shape

      subroutine assumed_size(n1, n2, ain, aout, ainout, ano)
        implicit none
        integer, intent(in) :: n1, n2
        character(*), dimension(n1, *), intent(in) :: ain
        character(*), dimension(n1, *), intent(out) :: aout
        character(*), dimension(n1, *), intent(inout) :: ainout
        character(*), dimension(n1, *) :: ano

        integer ll

        ll = len(ain)

        aout(:,1:n2) = ain(:,1:n2)
        ano(:,1:n2) = ainout(:,1:n2)
        ainout(:,1:n2) = ain(:,1:n2)(1:ll/2) // ano(:,1:n2)(ll/2+1:ll)
      end subroutine assumed_size
