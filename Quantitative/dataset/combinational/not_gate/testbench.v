`timescale 1ns / 1ps

module not_gate_tb;
    reg a;
    wire y;

    not_gate dut (
        .a(a),
        .y(y)
    );

    initial begin
        a = 0;
        #1;
        if (y !== 1'b1) begin
            $display("FAIL: a=0 y=%0b expected=1", y);
            $fatal;
        end

        a = 1;
        #1;
        if (y !== 1'b0) begin
            $display("FAIL: a=1 y=%0b expected=0", y);
            $fatal;
        end

        $display("PASS");
        $finish;
    end
endmodule

