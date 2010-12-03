subroutine singlechar(x, y, z)
      character, intent(in) :: x
      character, intent(inout) :: y
      character, intent(out) :: z
      z = char(ichar(x) + 1)
      y = char(ichar(y) + 1)
end subroutine
