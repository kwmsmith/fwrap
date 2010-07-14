      subroutine explicit_shape(n1, n2, ain, aout, ainout, ano)
        implicit none
        integer, intent(in) :: n1, n2
        integer, dimension(n1, n2), intent(in) :: ain
        integer, dimension(n1, n2), intent(out) :: aout
        integer, dimension(n1, n2), intent(inout) :: ainout
        integer, dimension(n1, n2) :: ano

        aout = ain
        ano = ainout
        ainout = ain + ano
      end subroutine explicit_shape

      subroutine assumed_shape(ain, aout, ainout, ano)
        implicit none
        integer, dimension(:, :), intent(in) :: ain
        integer, dimension(:, :), intent(out) :: aout
        integer, dimension(:, :), intent(inout) :: ainout
        integer, dimension(:, :) :: ano

        aout = ain
        ano = ainout
        ainout = ain + ano
      end subroutine assumed_shape

      subroutine assumed_size(n1, n2, ain, aout, ainout, ano)
        implicit none
        integer, intent(in) :: n1, n2
        integer, dimension(n1, *), intent(in) :: ain
        integer, dimension(n1, *), intent(out) :: aout
        integer, dimension(n1, *), intent(inout) :: ainout
        integer, dimension(n1, *) :: ano

        aout(:,1:n2) = ain(:,1:n2)
        ano(:,1:n2) = ainout(:,1:n2)
        ainout(:,1:n2) = ain(:,1:n2) + ano(:,1:n2)
      end subroutine assumed_size
