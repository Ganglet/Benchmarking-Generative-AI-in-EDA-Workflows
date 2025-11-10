`timescale 1ns / 1ps

module half_adder_tb;
    reg a;
    reg b;
    wire sum;
    wire carry;

    half_adder dut (
        .a(a),
        .b(b),
        .sum(sum),
        .carry(carry)
    );

    reg exp_sum;
    reg exp_carry;
    integer i;

    initial begin
        for (i = 0; i < 4; i = i + 1) begin
            {a, b} = i[1:0];
            {exp_carry, exp_sum} = a + b;
            #1;
            if (sum !== exp_sum || carry !== exp_carry) begin
                $display("FAIL: a=%0b b=%0b sum=%0b carry=%0b expected_sum=%0b expected_carry=%0b", a, b, sum, carry, exp_sum, exp_carry);
                $fatal;
            end
        end
        $display("PASS");
        $finish;
    end
endmodule

