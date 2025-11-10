`timescale 1ns / 1ps

module decoder_2to4_tb;
    reg en;
    reg [1:0] in;
    wire [3:0] out;

    decoder_2to4 dut (
        .en(en),
        .in(in),
        .out(out)
    );

    integer i;

    initial begin
        en = 1'b0;
        in = 2'b00;
        #1;
        if (out !== 4'b0000) begin
            $display("FAIL: enable low but out=%0b", out);
            $fatal;
        end

        en = 1'b1;
        for (i = 0; i < 4; i = i + 1) begin
            in = i[1:0];
            #1;
            if (out !== (4'b0001 << in)) begin
                $display("FAIL: in=%0b out=%0b expected=%0b", in, out, (4'b0001 << in));
                $fatal;
            end
        end

        $display("PASS");
        $finish;
    end
endmodule

