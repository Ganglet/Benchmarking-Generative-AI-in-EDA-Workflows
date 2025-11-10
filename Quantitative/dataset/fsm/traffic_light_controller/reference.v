`timescale 1ns / 1ps

module traffic_light_controller (
    input  wire clk,
    input  wire rst,
    output reg  [2:0] ns_light,
    output reg  [2:0] ew_light
);
    localparam RED    = 3'b100;
    localparam YELLOW = 3'b010;
    localparam GREEN  = 3'b001;

    localparam S_NS_GO  = 2'b00;
    localparam S_NS_WARN = 2'b01;
    localparam S_EW_GO  = 2'b10;
    localparam S_EW_WARN = 2'b11;

    reg [1:0] state;
    reg [1:0] next_state;
    reg [1:0] timer;

    always @(posedge clk) begin
        if (rst) begin
            state <= S_NS_GO;
            timer <= 2'b00;
        end else begin
            state <= next_state;
            if (state != next_state) begin
                timer <= 2'b00;
            end else begin
                timer <= timer + 1'b1;
            end
        end
    end

    always @(*) begin
        next_state = state;
        ns_light = RED;
        ew_light = RED;

        case (state)
            S_NS_GO: begin
                ns_light = GREEN;
                ew_light = RED;
                if (timer == 2'd2) begin
                    next_state = S_NS_WARN;
                end
            end
            S_NS_WARN: begin
                ns_light = YELLOW;
                ew_light = RED;
                if (timer == 2'd1) begin
                    next_state = S_EW_GO;
                end
            end
            S_EW_GO: begin
                ns_light = RED;
                ew_light = GREEN;
                if (timer == 2'd2) begin
                    next_state = S_EW_WARN;
                end
            end
            S_EW_WARN: begin
                ns_light = RED;
                ew_light = YELLOW;
                if (timer == 2'd1) begin
                    next_state = S_NS_GO;
                end
            end
            default: begin
                next_state = S_NS_GO;
            end
        endcase
    end
endmodule

