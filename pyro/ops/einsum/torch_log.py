from __future__ import absolute_import, division, print_function

import torch

from pyro.ops.einsum.util import Tensordot


def transpose(a, axes):
    return a.permute(axes)


def einsum(equation, *operands):
    """
    Log-sum-exp implementation of einsum.
    """
    # rename symbols to support PyTorch 0.4.1 and earlier,
    # which allow only symbols a-z.
    symbols = sorted(set(equation) - set(',->'))
    rename = dict(zip(symbols, 'abcdefghijklmnopqrstuvwxyz'))
    equation = ''.join(rename.get(s, s) for s in equation)

    inputs, output = equation.split('->')
    if inputs == output:
        return operands[0][...]  # create a new object
    inputs = inputs.split(',')

    shifts = []
    exp_operands = []
    for dims, operand in zip(inputs, operands):
        shift = operand
        for i, dim in enumerate(dims):
            if dim not in output:
                shift = shift.max(i, keepdim=True)[0]
        exp_operands.append((operand - shift).exp())

        # permute shift to match output
        shift = shift.reshape(torch.Size(size for size, dim in zip(operand.shape, dims)
                                         if dim in output))
        if shift.dim():
            shift = shift.reshape((1,) * (len(output) - shift.dim()) + shift.shape)
            dims = [dim for dim in dims if dim in output]
            dims = [dim for dim in output if dim not in dims] + dims
            shift = shift.permute(*(dims.index(dim) for dim in output))
        shifts.append(shift)

    result = torch.einsum(equation, exp_operands).log()
    return sum(shifts + [result])


tensordot = Tensordot(einsum)

__all__ = ["transpose", "einsum", "tensordot"]
