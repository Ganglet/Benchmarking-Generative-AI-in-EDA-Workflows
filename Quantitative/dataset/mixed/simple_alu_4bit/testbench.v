`timescale 1ns / 1ps

module simple_alu_4bit_tb;
    reg [3:0] a;
    reg [3:0] b;
    reg [1:0] op;
    wire [3:0] result;
    wire carry_out;
    wire zero;

    simple_alu_4bit dut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .carry_out(carry_out),
        .zero(zero)
    );

    integer i;
    reg [4:0] sum;
    reg [4:0] diff;

    task check;
        input [3:0] exp_result;
        input exp_carry;
        input exp_zero;
        begin
            #1;
            if (result !== exp_result || carry_out !== exp_carry || zero !== exp_zero) begin
                $display("FAIL: a=%0h b=%0h op=%0b result=%0h carry=%0b zero=%0b expected_result=%0h expected_carry=%0b expected_zero=%0b",
                         a, b, op, result, carry_out, zero, exp_result, exp_carry, exp_zero);
                $fatal;
            end
        end
    endtask

    initial begin
        for (i = 0; i < 16; i = i + 1) begin
            a = i[3:0];
            b = (15 - i)[3:0];

            op = 2'b00;
            sum = a + b;
            check(sum[3:0], sum[4], sum[3:0] == 4'h0);

            op = 2'b01;
            diff = {1'b0, a} - {1'b0, b};
            check(diff[3:0], diff[4], diff[3:0] == 4'h0);

            op = 2'b10;
            check(a & b, 1'b0, ((a & b) == 4'h0));

            op = 2'b11;
            check(a ^ b, 1'b0, ((a ^ b) == 4'h0));
        end

        $display("PASS");
        $finish;
    end
endmodule

