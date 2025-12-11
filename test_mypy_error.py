def test_function(x: int) -> int:
    # This references undefined variable to trigger mypy error
    return undefined_variable + x
