`timescale 1ns / 1ps

module xor_gate_tb;
    reg a;
    reg b;
    wire y;

    xor_gate dut (
        .a(a),
        .b(b),
        .y(y)
    );

    integer i;

    initial begin
        for (i = 0; i < 4; i = i + 1) begin
            {a, b} = i[1:0];
            #1;
            if (y !== (a ^ b)) begin
                $display("FAIL: a=%0b b=%0b y=%0b expected=%0b", a, b, y, (a ^ b));
                $fatal;
            end
        end
        $display("PASS");
        $finish;
    end
endmodule

