`timescale 1ns / 1ps

module full_adder_tb;
    reg a;
    reg b;
    reg cin;
    wire sum;
    wire cout;

    full_adder dut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    integer i;
    reg [1:0] expected;

    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            {a, b, cin} = i[2:0];
            #1;
            expected = a + b + cin;
            if ({cout, sum} !== {expected[1], expected[0]}) begin
                $display("FAIL: a=%0b b=%0b cin=%0b sum=%0b cout=%0b expected_sum=%0b expected_cout=%0b", a, b, cin, sum, cout, expected[0], expected[1]);
                $fatal;
            end
        end
        $display("PASS");
        $finish;
    end
endmodule

